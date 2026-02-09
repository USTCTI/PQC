import time
import yaml
import statistics
import os
import json
import psutil
import platform
from datetime import datetime
from typing import Dict, List, Any
import numpy as np

from .algorithms import get_algorithm, KEM, Signature
from .monitor import SystemMonitor
from .logger import setup_logger

logger = setup_logger("Runner")

class BenchmarkRunner:
    def __init__(self, config_path: str):
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        
        self.output_dir = self.config['execution'].get('output_dir', 'data')
        os.makedirs(self.output_dir, exist_ok=True)
        
        self.monitor = SystemMonitor(
            interval=self.config['monitoring']['sampling_interval_seconds'],
            output_file=os.path.join(self.output_dir, f"system_monitor_{int(time.time())}.json")
        )

    def _measure_time(self, func, *args) -> int:
        start = time.perf_counter_ns()
        func(*args)
        end = time.perf_counter_ns()
        return end - start

    def run_warmup(self, alg, iterations: int):
        logger.info(f"Warming up {alg.name} with {iterations} iterations...")
        # Simple warmup with KeyGen
        for _ in range(iterations):
            try:
                alg.keygen()
            except Exception:
                pass

    def run_micro_benchmarks(self, alg, alg_type: str, params: Dict[str, Any]) -> Dict[str, Any]:
        results = {}
        iterations = 1000 # Default if not specified, though config implies we should iterate enough
        # We can determine iterations dynamically or fixed. 
        # For now, let's use a fixed number or from config if available, but config didn't specify per-alg iterations explicitly in the example, 
        # so we'll use a reasonable default or a "min duration" approach.
        # Let's use 1000 for now.
        
        logger.info(f"Running micro-benchmarks for {alg.name}...")
        
        # 1. KeyGen
        latencies = []
        for _ in range(iterations):
            latencies.append(self._measure_time(alg.keygen))
        
        results['keygen'] = self._calculate_stats(latencies)

        # Generate a keypair for next steps
        pk, sk = alg.keygen()

        # 2. Encaps/Sign & Decaps/Verify
        if alg_type == 'kem':
            payload_sizes = params.get('payload_sizes', [32])
            for size in payload_sizes:
                # Encaps
                enc_latencies = []
                dec_latencies = []
                for _ in range(iterations):
                    # For KEM, usually encaps doesn't take payload message in standard KEM (it generates shared secret), 
                    # but some variations or hybrid modes might. 
                    # Standard NIST KEM: encaps(pk) -> (ct, ss). No input message.
                    # The user config says "payload_sizes" for KEM "simulated messages for encapsulation".
                    # This might imply KEM-based encryption (PKE) or just measuring if size matters (it shouldn't for pure KEM).
                    # We will follow standard KEM interface: encaps(pk). If user meant PKE, we'd need encrypt(pk, msg).
                    # Assuming standard KEM for now. If payload_size is relevant, maybe it's for PKE.
                    # We will proceed with standard encaps(pk).
                    
                    t0 = time.perf_counter_ns()
                    ct, ss = alg.encaps(pk)
                    t1 = time.perf_counter_ns()
                    enc_latencies.append(t1 - t0)
                    
                    t0 = time.perf_counter_ns()
                    _ = alg.decaps(ct, sk)
                    t1 = time.perf_counter_ns()
                    dec_latencies.append(t1 - t0)
                
                results[f'encaps_size_{size}'] = self._calculate_stats(enc_latencies)
                results[f'decaps_size_{size}'] = self._calculate_stats(dec_latencies)

        elif alg_type == 'sign':
            message_sizes = params.get('message_sizes', [32])
            for size in message_sizes:
                message = os.urandom(size)
                sign_latencies = []
                verify_latencies = []
                
                for _ in range(iterations):
                    t0 = time.perf_counter_ns()
                    sig = alg.sign(message, sk)
                    t1 = time.perf_counter_ns()
                    sign_latencies.append(t1 - t0)
                    
                    t0 = time.perf_counter_ns()
                    alg.verify(pk, message, sig)
                    t1 = time.perf_counter_ns()
                    verify_latencies.append(t1 - t0)

                results[f'sign_size_{size}'] = self._calculate_stats(sign_latencies)
                results[f'verify_size_{size}'] = self._calculate_stats(verify_latencies)

        return results

    def _calculate_stats(self, latencies_ns: List[int]) -> Dict[str, float]:
        # Convert to microseconds
        latencies = [l / 1000.0 for l in latencies_ns]
        return {
            "avg_us": statistics.mean(latencies),
            "median_us": statistics.median(latencies),
            "p99_us": np.percentile(latencies, 99),
            "min_us": min(latencies),
            "max_us": max(latencies),
            "std_dev_us": statistics.stdev(latencies) if len(latencies) > 1 else 0,
            "throughput_ops_sec": 1000000.0 / statistics.mean(latencies) if statistics.mean(latencies) > 0 else 0
        }

    def run_long_stability_test(self, algs: List[Any], duration: int):
        logger.info(f"Starting long-running stability test for {duration} seconds...")
        start_time = time.time()
        end_time = start_time + duration
        
        # Prepare instances
        instances = []
        for alg_conf in algs:
            # Re-instantiate or reuse? Reuse is fine.
            pass

        # We will cycle through algorithms and perform operations
        iteration = 0
        while time.time() < end_time:
            for alg_obj in algs:
                # Perform a full cycle: KeyGen -> Encaps/Sign -> Decaps/Verify
                try:
                    pk, sk = alg_obj.keygen()
                    if isinstance(alg_obj, KEM):
                         ct, ss = alg_obj.encaps(pk)
                         alg_obj.decaps(ct, sk)
                    elif isinstance(alg_obj, Signature):
                         msg = os.urandom(32)
                         sig = alg_obj.sign(msg, sk)
                         alg_obj.verify(pk, msg, sig)
                except Exception as e:
                    logger.error(f"Error in stability test for {alg_obj.name}: {e}")
            
            iteration += 1
            if iteration % 100 == 0:
                 logger.debug(f"Stability test progress: {int(time.time() - start_time)}/{duration}s")
        
        logger.info("Stability test completed.")

    def run(self):
        # Pre-flight check
        initial_cpu = psutil.cpu_percent(interval=1)
        if initial_cpu > 20.0:
            logger.warning(f"High system CPU usage detected ({initial_cpu}%). Benchmark results may be affected.")
        else:
            logger.info(f"System CPU usage is normal ({initial_cpu}%). Starting benchmark.")

        # Start Monitor
        self.monitor.start()
        
        full_results = {
            "metadata": {
                "start_time": datetime.now().isoformat(),
                "platform": platform.platform(),
                "processor": platform.processor(),
                "config": self.config
            },
            "micro_benchmarks": {}
        }

        try:
            # 1. KEMs
            if 'kem' in self.config['algorithms']:
                for item in self.config['algorithms']['kem']:
                    alg = get_algorithm('kem', item['name'], item['implementation'])
                    self.run_warmup(alg, self.config['execution']['warmup_iterations'])
                    res = self.run_micro_benchmarks(alg, 'kem', item)
                    full_results['micro_benchmarks'][item['name']] = res
                    
            # 2. Signatures
            if 'sign' in self.config['algorithms']:
                for item in self.config['algorithms']['sign']:
                    alg = get_algorithm('sign', item['name'], item['implementation'])
                    self.run_warmup(alg, self.config['execution']['warmup_iterations'])
                    res = self.run_micro_benchmarks(alg, 'sign', item)
                    full_results['micro_benchmarks'][item['name']] = res

            # 3. Stability Test
            # Collect all algorithms for mixed execution
            all_algs = []
            if 'kem' in self.config['algorithms']:
                for item in self.config['algorithms']['kem']:
                     all_algs.append(get_algorithm('kem', item['name'], item['implementation']))
            if 'sign' in self.config['algorithms']:
                for item in self.config['algorithms']['sign']:
                     all_algs.append(get_algorithm('sign', item['name'], item['implementation']))
            
            self.run_long_stability_test(all_algs, self.config['execution']['long_run_duration_seconds'])

        except KeyboardInterrupt:
            logger.info("Benchmark interrupted by user.")
        except Exception as e:
            logger.error(f"Benchmark failed: {e}", exc_info=True)
        finally:
            self.monitor.stop()
            full_results["metadata"]["end_time"] = datetime.now().isoformat()
            
            # Save results
            res_file = os.path.join(self.output_dir, f"benchmark_results_{int(time.time())}.json")
            with open(res_file, 'w') as f:
                json.dump(full_results, f, indent=2)
            logger.info(f"Results saved to {res_file}")

if __name__ == "__main__":
    # Basic test
    pass

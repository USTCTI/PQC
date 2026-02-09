import psutil
import time
import threading
import platform
import subprocess
import json
from typing import List, Dict, Any
from .logger import setup_logger

logger = setup_logger("Monitor")

class SystemMonitor:
    def __init__(self, interval: float = 1.0, output_file: str = None):
        self.interval = interval
        self.output_file = output_file
        self.stop_event = threading.Event()
        self.data_points: List[Dict[str, Any]] = []
        self.thread = None
        self.is_macos = platform.system() == "Darwin"

    def start(self):
        self.stop_event.clear()
        self.thread = threading.Thread(target=self._monitor_loop)
        self.thread.daemon = True
        self.thread.start()
        logger.info(f"System monitor started with interval {self.interval}s")

    def stop(self):
        self.stop_event.set()
        if self.thread:
            self.thread.join()
        logger.info("System monitor stopped")
        if self.output_file:
            self._save_data()

    def _monitor_loop(self):
        process = psutil.Process()
        while not self.stop_event.is_set():
            timestamp = time.time()
            
            # Basic Metrics via psutil
            cpu_percent = process.cpu_percent(interval=None) # Non-blocking if called repeatedly, but first call might be 0. 
            # Actually process.cpu_percent needs interval or previous call. 
            # Better to use psutil.cpu_percent(interval=None) for system wide or process specific?
            # User asked for "Process CPU usage" and "Energy impact".
            # "CPU占用率：进程在整个测试期间及峰值时刻的CPU使用百分比" -> Process CPU.
            
            try:
                mem_info = process.memory_info()
                memory_rss = mem_info.rss  # bytes
            except psutil.NoSuchProcess:
                break

            metrics = {
                "timestamp": timestamp,
                "cpu_percent": cpu_percent,
                "memory_rss": memory_rss,
                "system_cpu_percent": psutil.cpu_percent(interval=None)
            }

            # Extended metrics (Frequency/Temp)
            # On macOS M4, we might parse powermetrics, but that requires sudo and is complex to parse in real-time within python without a sidecar.
            # We will use psutil.cpu_freq() if available.
            try:
                freq = psutil.cpu_freq()
                if freq:
                    metrics["cpu_freq_current"] = freq.current
            except Exception:
                pass

            self.data_points.append(metrics)
            time.sleep(self.interval)

    def _save_data(self):
        try:
            with open(self.output_file, 'w') as f:
                # Write as JSON Lines or a single JSON array
                json.dump(self.data_points, f, indent=2)
            logger.info(f"Monitor data saved to {self.output_file}")
        except Exception as e:
            logger.error(f"Failed to save monitor data: {e}")

    def get_summary(self) -> Dict[str, float]:
        if not self.data_points:
            return {}
        
        df_data = {
            "cpu_percent": [x["cpu_percent"] for x in self.data_points],
            "memory_rss": [x["memory_rss"] for x in self.data_points]
        }
        
        summary = {
            "avg_cpu_percent": sum(df_data["cpu_percent"]) / len(df_data["cpu_percent"]),
            "max_cpu_percent": max(df_data["cpu_percent"]),
            "max_memory_rss": max(df_data["memory_rss"]),
            "avg_memory_rss": sum(df_data["memory_rss"]) / len(df_data["memory_rss"])
        }
        return summary

import argparse
import sys
import signal
import logging
from src.runner import BenchmarkRunner
from src.logger import setup_logger

def signal_handler(sig, frame):
    logging.info("Received interrupt signal. Exiting gracefully...")
    # The runner handles KeyboardInterrupt/stopping via exception or flags if needed, 
    # but since we run blocking tasks, the exception is the main way to catch Ctrl+C.
    # If this handler is installed, it might prevent KeyboardInterrupt exception in main thread 
    # depending on how python handles it. 
    # Actually default python SIGINT handler raises KeyboardInterrupt.
    # We can rely on that or set a custom one that just logs and maybe sets a flag if we had a global one.
    # For now, we rely on the Runner's try-except KeyboardInterrupt.
    pass

def main():
    parser = argparse.ArgumentParser(description="PQC Benchmark Suite for Apple Silicon M4")
    parser.add_argument(
        "--config", 
        type=str, 
        default="config/config.yaml", 
        help="Path to the configuration file"
    )
    args = parser.parse_args()

    # Setup global logger first (basic console)
    logger = setup_logger("Main")
    
    logger.info(f"Starting PQC Benchmark Suite using config: {args.config}")

    try:
        runner = BenchmarkRunner(args.config)
        runner.run()
    except FileNotFoundError:
        logger.error(f"Configuration file not found: {args.config}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}", exc_info=True)
        sys.exit(1)
    
    logger.info("Benchmark process finished.")

if __name__ == "__main__":
    main()

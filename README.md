# PQC Benchmark Suite for Apple Silicon M4

This project provides an automated, configurable benchmark suite for Post-Quantum Cryptography (PQC) algorithms, specifically optimized for testing on Apple Silicon (M4) platforms. It is designed to evaluate NIST-standardized algorithms (ML-KEM, ML-DSA, Falcon, SPHINCS+) in terms of performance, resource consumption, and stability.

## Features

- **Modular Architecture**: 
  - Pluggable algorithm backend (currently supports `pqcrypto`).
  - Extensible monitoring and reporting modules.
- **Configurable Workflow**: 
  - Fully driven by `config/config.yaml`.
  - Adjustable payload sizes, iteration counts, and test duration.
- **Comprehensive Metrics**: 
  - **Latency**: Average, Median, P99, Min, Max, Standard Deviation.
  - **Throughput**: Operations per second.
  - **System Resources**: Real-time CPU and Memory usage monitoring.
- **Stability Testing**: 
  - Long-running (e.g., 1 hour) mixed workload tests to detect thermal throttling or performance drift.
- **Automated Reporting**: 
  - Generates professional PDF reports with executive summaries, detailed data tables, and visualization charts (Latency Boxplots, Throughput Bar Charts).

## Prerequisites

- **Hardware**: Apple Silicon (M4/M3/M2/M1) device recommended for intended performance analysis.
- **OS**: macOS (tested), Linux, or Windows.
- **Python**: Version 3.9 or higher.

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repository_url>
   cd PQC-Benchmark-Suite
   ```

2. **Create and activate a virtual environment** (Highly Recommended):
   ```bash
   # macOS/Linux
   python3 -m venv venv
   source venv/bin/activate

   # Windows
   python -m venv venv
   .\venv\Scripts\Activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
   *Note: This will install `pqcrypto`, `psutil`, `pandas`, `matplotlib`, `fpdf2` and other necessary libraries.*

## Usage

### 1. Configuration

Edit `config/config.yaml` to customize your benchmark run.

*   **Algorithms**: Enable/disable specific algorithms (e.g., `ML-KEM-512`, `ML-DSA-44`).
*   **Execution**:
    *   `warmup_iterations`: Number of runs to warm up the cache (default: 100).
    *   `long_run_duration_seconds`: Duration for the stability test (e.g., `3600` for 1 hour, `60` for a quick check).
*   **Monitoring**: Adjust sampling interval (default: 1.0s).

### 2. Run Benchmark

Execute the main script to start the testing process:

```bash
python main.py --config config/config.yaml
```

**What happens during execution:**
1.  **System Check**: Verifies initial CPU usage to ensure a clean environment.
2.  **Warmup**: Executes algorithms briefly to prime the CPU cache.
3.  **Micro-benchmarks**: Measures latency and throughput for KeyGen, Encaps/Sign, and Decaps/Verify operations.
4.  **Stability Test**: Runs a continuous mixed workload for the configured duration.
5.  **Data Saving**: 
    *   Benchmark results -> `data/benchmark_results_<timestamp>.json`
    *   System monitor logs -> `data/system_monitor_<timestamp>.json`

### 3. Generate Analysis Report

After the benchmark completes, use the analysis tool to generate a PDF report:

```bash
# Automatically use the latest result file in data/
python analysis/generate_report.py
```

Or specify a specific result file:

```bash
python analysis/generate_report.py --data data/benchmark_results_1717123456.json
```

The report will be saved to: `analysis_output/benchmark_report.pdf`

## Project Structure

```
PQC-Benchmark-Suite/
├── config/
│   └── config.yaml          # Test configuration (algorithms, duration, etc.)
├── src/
│   ├── __init__.py
│   ├── algorithms.py        # Algorithm wrappers and NIST mapping
│   ├── logger.py            # Logging configuration
│   ├── monitor.py           # System resource monitor (CPU/RAM)
│   └── runner.py            # Main test execution engine
├── analysis/
│   └── generate_report.py   # Data analysis and PDF generation script
├── data/                    # Output directory for raw JSON data
├── analysis_output/         # Output directory for generated PDF reports
├── main.py                  # Entry point script
├── requirements.txt         # Project dependencies
└── README.md                # Project documentation
```

## Supported Algorithms

The suite currently maps the following NIST standardized names to the `pqcrypto` implementation:

*   **KEM (Key Encapsulation Mechanisms)**:
    *   ML-KEM-512 (Kyber-512)
    *   ML-KEM-768 (Kyber-768)
*   **Digital Signatures**:
    *   ML-DSA-44 (Dilithium2)
    *   ML-DSA-65 (Dilithium3)
    *   Falcon-512
    *   SPHINCS+-128s-simple

## Notes for Apple Silicon Users

*   **Performance Variability**: For the most accurate stability results, ensure the device is plugged into power and "Low Power Mode" is disabled.
*   **Thermal Monitoring**: The tool captures CPU frequency and thermal throttling indicators where available via standard APIs.
*   **Dependencies**: Ensure your `pqcrypto` installation matches your architecture (arm64). `pip` usually handles this automatically with pre-built wheels.

## License

[License Name] - See LICENSE file for details.

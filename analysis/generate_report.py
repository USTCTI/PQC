import argparse
import json
import os
import glob
import matplotlib.pyplot as plt
import pandas as pd
from fpdf import FPDF
from datetime import datetime

class ReportGenerator:
    def __init__(self, result_file: str, output_dir: str = "analysis_output"):
        self.result_file = result_file
        self.output_dir = output_dir
        with open(result_file, 'r') as f:
            self.data = json.load(f)
        os.makedirs(self.output_dir, exist_ok=True)

    def generate_charts(self):
        charts = []
        
        # 1. Throughput Comparison (Bar Chart)
        micro_benchmarks = self.data.get("micro_benchmarks", {})
        algs = []
        throughputs = []
        
        for alg_name, res in micro_benchmarks.items():
            # For simplicity, pick keygen throughput or average of all ops
            # Let's pick keygen as a common baseline
            if "keygen" in res:
                algs.append(alg_name)
                throughputs.append(res["keygen"]["throughput_ops_sec"])
        
        if algs:
            plt.figure(figsize=(10, 6))
            plt.bar(algs, throughputs, color='skyblue')
            plt.title('Key Generation Throughput (Ops/Sec)')
            plt.xlabel('Algorithm')
            plt.ylabel('Throughput (Ops/Sec)')
            plt.xticks(rotation=45)
            plt.tight_layout()
            chart_path = os.path.join(self.output_dir, "throughput_comparison.png")
            plt.savefig(chart_path)
            plt.close()
            charts.append(("Throughput Comparison", chart_path))

        # 2. Latency Boxplots (Mocked since we stored stats not raw data in JSON for microbenchmarks)
        # Ideally we should store raw data or percentiles. 
        # We stored p99, median, avg, min, max. We can plot these as a "candlestick" or error bar.
        # Let's plot Average Latency with Error Bars (Std Dev)
        
        avg_latencies = []
        std_devs = []
        names = []
        
        for alg_name, res in micro_benchmarks.items():
            if "keygen" in res:
                names.append(alg_name)
                avg_latencies.append(res["keygen"]["avg_us"])
                std_devs.append(res["keygen"]["std_dev_us"])
                
        if names:
            plt.figure(figsize=(10, 6))
            plt.bar(names, avg_latencies, yerr=std_devs, capsize=5, color='lightgreen')
            plt.title('Average KeyGen Latency (µs)')
            plt.ylabel('Time (µs)')
            plt.xticks(rotation=45)
            plt.tight_layout()
            chart_path = os.path.join(self.output_dir, "latency_comparison.png")
            plt.savefig(chart_path)
            plt.close()
            charts.append(("Latency Comparison", chart_path))

        return charts

    def generate_pdf(self, charts):
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        
        # Title
        pdf.set_font("Arial", 'B', 16)
        pdf.cell(200, 10, txt="PQC Benchmark Analysis Report", ln=True, align='C')
        pdf.ln(10)
        
        # Metadata
        pdf.set_font("Arial", size=10)
        meta = self.data.get("metadata", {})
        pdf.cell(200, 10, txt=f"Date: {meta.get('start_time')}", ln=True)
        pdf.cell(200, 10, txt=f"Platform: {meta.get('platform')}", ln=True)
        pdf.ln(10)
        
        # Executive Summary
        pdf.set_font("Arial", 'B', 14)
        pdf.cell(200, 10, txt="1. Executive Summary", ln=True)
        pdf.set_font("Arial", size=11)
        pdf.multi_cell(0, 10, txt="This report presents the performance benchmarks of selected Post-Quantum Cryptography algorithms. "
                                  "The following charts illustrate the throughput and latency characteristics.")
        pdf.ln(5)

        # Charts
        pdf.set_font("Arial", 'B', 14)
        pdf.cell(200, 10, txt="2. Performance Charts", ln=True)
        
        for title, path in charts:
            pdf.set_font("Arial", 'B', 12)
            pdf.cell(200, 10, txt=title, ln=True)
            pdf.image(path, w=170)
            pdf.ln(5)

        # Detailed Stats Table (Simplified)
        pdf.add_page()
        pdf.set_font("Arial", 'B', 14)
        pdf.cell(200, 10, txt="3. Detailed Statistics", ln=True)
        pdf.set_font("Courier", size=8)
        
        # Header
        col_width = 25
        headers = ["Algorithm", "Op", "Avg(us)", "P99(us)", "Throughput"]
        for h in headers:
            pdf.cell(col_width, 10, h, border=1)
        pdf.ln()
        
        micro_benchmarks = self.data.get("micro_benchmarks", {})
        for alg_name, ops in micro_benchmarks.items():
            for op_name, stats in ops.items():
                pdf.cell(col_width, 10, alg_name[:12], border=1)
                pdf.cell(col_width, 10, op_name[:12], border=1)
                pdf.cell(col_width, 10, f"{stats['avg_us']:.2f}", border=1)
                pdf.cell(col_width, 10, f"{stats['p99_us']:.2f}", border=1)
                pdf.cell(col_width, 10, f"{stats['throughput_ops_sec']:.0f}", border=1)
                pdf.ln()

        output_path = os.path.join(self.output_dir, "benchmark_report.pdf")
        pdf.output(output_path)
        return output_path

def main():
    parser = argparse.ArgumentParser(description="Generate PQC Analysis Report")
    parser.add_argument("--data", type=str, help="Path to JSON result file")
    args = parser.parse_args()
    
    data_file = args.data
    if not data_file:
        # Find latest in data/
        list_of_files = glob.glob('data/benchmark_results_*.json')
        if not list_of_files:
            print("No data file found in data/. Please run benchmark first.")
            return
        data_file = max(list_of_files, key=os.path.getctime)
        print(f"Using latest data file: {data_file}")

    generator = ReportGenerator(data_file)
    charts = generator.generate_charts()
    report_path = generator.generate_pdf(charts)
    print(f"Report generated at: {report_path}")

if __name__ == "__main__":
    main()

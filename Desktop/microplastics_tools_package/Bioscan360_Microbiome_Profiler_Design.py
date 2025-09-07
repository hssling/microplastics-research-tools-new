from fpdf import FPDF
import datetime

# Create a PDF document with the detailed design
pdf = FPDF()
pdf.add_page()
pdf.set_font("Arial", size=12)

# Title
pdf.set_font("Arial", 'B', 16)
pdf.cell(200, 10, txt="BioScan 360™ - Human Microbiome Profiler and Predictor", ln=True, align='C')
pdf.set_font("Arial", size=12)
pdf.cell(200, 10, txt=f"Design Document - {datetime.datetime.now().strftime('%Y-%m-%d')}", ln=True, align='C')
pdf.ln(10)

# Section 1: Overview
pdf.set_font("Arial", 'B', 14)
pdf.cell(200, 10, txt="1. Overview", ln=True)
pdf.set_font("Arial", size=12)
pdf.multi_cell(0, 10, txt=(
    "BioScan 360™ is a state-of-the-art medical diagnostic device capable of profiling the human microbiome "
    "through DNA/RNA sequencing and predicting disease outcomes using AI-powered analytics. It integrates biological "
    "sampling, next-generation sequencing (NGS), real-time health dashboard, and cloud connectivity for medical-grade "
    "insights and preventive care."
))

# Section 2: Components
pdf.set_font("Arial", 'B', 14)
pdf.cell(200, 10, txt="2. Components", ln=True)
pdf.set_font("Arial", size=12)
components = [
    "1. Smart Sample Collector (swabs, stool container, auto-sealing)",
    "2. DNA/RNA Sequencer (16S/18S rRNA, metagenomics capable)",
    "3. Biomarker Integration Chamber (optional blood biomarker reader)",
    "4. AI-Powered Analyzer Unit (with health prediction ML models)",
    "5. Touchscreen Interface (Dashboard + Doctor Mode)",
    "6. Wireless Health Cloud Sync Module (secure cloud integration)",
    "7. Power Supply Unit (UPS-integrated medical-grade)",
]
for comp in components:
    pdf.cell(200, 10, txt=comp, ln=True)

# Section 3: Electronic Circuitry
pdf.set_font("Arial", 'B', 14)
pdf.cell(200, 10, txt="3. Electronic Circuitry (Block-Level)", ln=True)
pdf.set_font("Arial", size=12)
pdf.multi_cell(0, 10, txt=(
    "- Microcontroller Unit: STM32 or Raspberry Pi Compute Module\n"
    "- Sequencer Interface: High-speed USB 3.0 or PCIe for NGS data\n"
    "- AI Accelerator: NVIDIA Jetson or Coral Edge TPU\n"
    "- Sensor Modules: Temperature, Sample Presence, QR Scanner\n"
    "- Touchscreen Driver: I2C/USB connected capacitive interface\n"
    "- Wi-Fi + BLE Module: ESP32-based or Qualcomm chipset\n"
    "- Power: Isolated 12V and 5V rails, surge protected\n"
))

# Section 4: Software Architecture
pdf.set_font("Arial", 'B', 14)
pdf.cell(200, 10, txt="4. Software Architecture", ln=True)
pdf.set_font("Arial", size=12)
pdf.multi_cell(0, 10, txt=(
    "- OS: Linux (Debian-based) with Docker containers\n"
    "- NGS Pipeline: QIIME2, Kraken2, MetaPhlAn3\n"
    "- Host Impact Analysis: Jupyter-based gene expression comparison\n"
    "- AI/ML Model: Trained in TensorFlow, served via Flask API\n"
    "- UI: React-based dashboard for touch interface\n"
    "- Cloud Sync: Encrypted HTTPS APIs with secure health data sync\n"
))

# Section 5: Use Cases
pdf.set_font("Arial", 'B', 14)
pdf.cell(200, 10, txt="5. Use Cases", ln=True)
pdf.set_font("Arial", size=12)
use_cases = [
    "- Preventive health diagnostics",
    "- Personalized nutrition & lifestyle",
    "- Gut-brain axis monitoring for mental health",
    "- Cancer and chronic inflammation risk profiling",
    "- Post-antibiotic flora recovery tracking"
]
for uc in use_cases:
    pdf.cell(200, 10, txt=uc, ln=True)

# Save the PDF
output_path = r"C:\Users\hssli\Downloads\BioScan360_Microbiome_Profiler_Design.pdf"
pdf.output(output_path)
print(f"PDF saved to: {output_path}")

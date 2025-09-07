
import os
import pdfplumber
from fpdf import FPDF

# ==== EXTRACT CONTENT FROM PDF ====
pdf_path = "DietaryGuidelinesforNINwebsite.pdf"
extracted_chapters = {}
if os.path.exists(pdf_path):
    with pdfplumber.open(pdf_path) as pdf:
        text = ""
        for page in pdf.pages:
            text += page.extract_text() + "\n"
    # Simple split by guideline/chapter headings (customize as needed)
    import re
    chapter_titles = re.findall(r"Guideline \d+:.*|Introduction|Current Diet and Nutrition Scenario|Dietary Goals|Elderly Nutrition", text)
    for i, title in enumerate(chapter_titles):
        start = text.find(title)
        end = text.find(chapter_titles[i+1]) if i+1 < len(chapter_titles) else len(text)
        chapter_text = text[start:end].strip()
        # Extract high-yield bullet points (customize extraction as needed)
        points = re.findall(r"•.*", chapter_text)
        if not points:
            # fallback: split by lines
            points = [line.strip() for line in chapter_text.split('\n') if len(line.strip()) > 10]
        extracted_chapters[title] = points[:8]  # take top 8 points for high yield

# ==== CONTENT FOR ALL CHAPTERS ====
if extracted_chapters:
    chapters = extracted_chapters
else:
    chapters = {
        "Guideline 15: Elderly Nutrition": [
            "Elderly need nutrient-dense, easily digestible foods."
        ]
    }
    for point in points[:3]:  # first 3 points as summary

# ==== CREATE FOLDER FOR PPTS ====

# ==== CREATE PDF OUTPUT ====
pdf = FPDF()
pdf.set_auto_page_break(auto=True, margin=15)
pdf.add_page()
pdf.set_font("Arial", 'B', 16)
pdf.cell(0, 10, "BIoscan Device Design", ln=True, align='C')
pdf.set_font("Arial", size=12)

for chapter, points in chapters.items():
    pdf.ln(8)
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(0, 10, chapter, ln=True)
    pdf.set_font("Arial", size=12)
    for point in points:
        pdf.multi_cell(0, 8, f"- {point}")

pdf.output("BIoscan_device_design.pdf")
print("PDF created: BIoscan_device_design.pdf")

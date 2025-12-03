# ----------------------------
# FILE: graph_report.py
# Clean PDF Report Generator with Pie Chart + Master List
# ----------------------------
import matplotlib.pyplot as plt
import pandas as pd
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle,
    Paragraph, Spacer, Image
)
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.utils import ImageReader


# ------------------------------------------------
# Compute age from birthdate
# ------------------------------------------------
def compute_age(birthdate_str):
    try:
        birth = datetime.strptime(birthdate_str, "%Y-%m-%d")
        today = datetime.today()
        age = today.year - birth.year - ((today.month, today.day) < (birth.month, birth.day))
        return max(age, 0)
    except:
        return 0


# ------------------------------------------------
# Build AGE GROUPS for pie chart
# ------------------------------------------------
def age_groups(df):
    groups = {
        "0–12": 0,
        "13–19": 0,
        "20–35": 0,
        "36–59": 0,
        "60+": 0
    }

    for age in df["age"]:
        if age <= 12:
            groups["0–12"] += 1
        elif age <= 19:
            groups["13–19"] += 1
        elif age <= 35:
            groups["20–35"] += 1
        elif age <= 59:
            groups["36–59"] += 1
        else:
            groups["60+"] += 1

    return groups


# ------------------------------------------------
# Generate PIE CHART
# ------------------------------------------------
def generate_pie_chart(df, out_png="age_pie.png"):
    groups = age_groups(df)
    labels = list(groups.keys())
    sizes = list(groups.values())

    plt.figure(figsize=(5, 5))
    plt.pie(sizes, labels=labels, autopct='%1.1f%%')
    plt.title("Age Group Distribution")
    plt.tight_layout()
    plt.savefig(out_png)
    plt.close()
    return out_png


# ------------------------------------------------
# Generate PDF with:
# ✔ Pie chart
# ✔ Total count
# ✔ Clean master list table
# ------------------------------------------------
def generate_pdf_report(df, pdf_path="report.pdf"):
    if df is None or df.empty:
        raise ValueError("No patient data available.")

    # ---- CLEAN THE DATAFRAME ----
    # Remove ID column if still present
    if "id" in df.columns:
        df = df.drop(columns=["id"])

    # Compute ages from birthdate if needed
    if "birthdate" in df.columns:
        df["age"] = df["birthdate"].apply(compute_age)

    # Full name column
    df["full_name"] = df["first_name"].astype(str) + " " + \
                      df["middle_name"].astype(str) + " " + \
                      df["last_name"].astype(str) + " " + \
                      df["name_ext"].astype(str)

    # Select master list columns (customize whenever)
    table_df = df[[
        "full_name","birthdate", "age", "contact", "address", "diagnosis", "notes"
    ]]

    # ---- CREATE CHART ----
    chart_path = generate_pie_chart(df)

    # ---- PDF DOCUMENT ----
    doc = SimpleDocTemplate(pdf_path, pagesize=A4)
    styles = getSampleStyleSheet()
    story = []

    # ----- TITLE -----
    story.append(Paragraph("<b>Patient Management Report</b>", styles['Title']))
    story.append(Spacer(1, 12))

    # ----- TOTAL COUNT -----
    total_patients = len(df)
    story.append(Paragraph(f"<b>Total Patients:</b> {total_patients}", styles['Normal']))
    story.append(Spacer(1, 12))

    # ----- AGE PIE CHART -----
    story.append(Paragraph("<b>Age Group Distribution</b>", styles['Heading2']))
    story.append(Image(chart_path, width=300, height=300))
    story.append(Spacer(1, 20))

    # ----- MASTER LIST -----
    story.append(Paragraph("<b>Master Patient List</b>", styles['Heading2']))
    story.append(Spacer(1, 10))

    table_data = [table_df.columns.tolist()] + table_df.values.tolist()

    table = Table(table_data, repeatRows=1)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#2c3e50")),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.whitesmoke, colors.lightgrey]),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
    ]))

    story.append(table)

    # ---- GENERATE PDF ----
    doc.build(story)
    return pdf_path

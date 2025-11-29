# ----------------------------
# FILE: graph_report.py
# Improved PDF Report Generator with Platypus
# ----------------------------
import matplotlib.pyplot as plt
import io
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from data_utils import dataframe_summary
from reportlab.platypus import Table, TableStyle, SimpleDocTemplate, Spacer, Paragraph, Image
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
import pandas as pd


# ----------------------------
# Histogram helper
# ----------------------------
def np_histogram(ages, bins):
    s = pd.Series(ages)
    counts = []
    edges = list(bins)
    for i in range(len(bins)-1):
        lo, hi = bins[i], bins[i+1]
        c = s[(s >= lo) & (s < hi)].count()
        counts.append(int(c))
    return counts, edges


# ----------------------------
# Chart Generator
# ----------------------------
def generate_patient_chart(df, out_png='chart.png'):
    if df.empty:
        raise ValueError("DataFrame is empty")

    ages = df['age'].fillna(0).astype(int)
    bins = [0,10,20,30,40,50,60,100]
    counts, edges = np_histogram(ages, bins)

    fig, ax = plt.subplots(figsize=(6, 3))
    ax.bar(range(len(counts)), counts)
    ax.set_xticks(range(len(counts)))
    ax.set_xticklabels([f"{edges[i]}-{edges[i+1]-1}" for i in range(len(edges)-1)])
    ax.set_title("Age Distribution")
    ax.set_ylabel("Patients")

    plt.tight_layout()
    fig.savefig(out_png)
    plt.close(fig)

    return out_png


# ----------------------------
# **NEW** Clean PDF Report Generator (Platypus)
# ----------------------------
def generate_pdf_report(df, pdf_path='report.pdf'):
    if df is None or df.empty:
        raise ValueError('DataFrame is empty or None')

    # Step 1: Create chart
    chart_file = 'tmp_chart.png'
    plt.figure(figsize=(6,3))
    df['age'].plot(kind='hist', bins=[0,10,20,30,40,50,60,100])
    plt.title('Age Distribution')
    plt.xlabel('Age')
    plt.ylabel('Number of Patients')
    plt.tight_layout()
    plt.savefig(chart_file)
    plt.close()

    # Step 2: Create PDF
    c = canvas.Canvas(pdf_path, pagesize=A4)
    width, height = A4
    c.setFont('Helvetica-Bold', 16)
    c.drawString(40, height-40, 'Patient Management Report')

    # Insert chart
    img = ImageReader(chart_file)
    c.drawImage(img, 40, height-250, width=500, height=150, preserveAspectRatio=True, mask='auto')

    # Step 3: Add patient table
    table_data = [df.columns.tolist()] + df.values.tolist()
    table = Table(table_data, repeatRows=1)

    # Styling
    style = TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.grey),
        ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 8),
        ('BOTTOMPADDING', (0,0), (-1,0), 6),
        ('GRID', (0,0), (-1,-1), 0.5, colors.black),
    ])
    table.setStyle(style)

    # Draw table
    table.wrapOn(c, width, height)
    table.drawOn(c, 40, height-450)

    c.showPage()
    c.save()
    return pdf_path
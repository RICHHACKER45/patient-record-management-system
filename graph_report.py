# ----------------------------
# FILE: graph_report.py
# Creates charts with matplotlib and PDF reports using reportlab.
# ----------------------------
import matplotlib.pyplot as plt
import io
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader

def generate_patient_chart(df, out_png='chart.png'):
    # Example: age distribution bar chart
    if df.empty:
        raise ValueError('DataFrame is empty')
    ages = df['age'].fillna(0).astype(int)
    bins = [0,10,20,30,40,50,60,100]
    counts, edges = np_histogram(ages, bins)
    fig, ax = plt.subplots(figsize=(6,3))
    ax.bar(range(len(counts)), counts)
    ax.set_xticks(range(len(counts)))
    ax.set_xticklabels([f'{edges[i]}-{edges[i+1]-1}' for i in range(len(edges)-1)])
    ax.set_ylabel('Number of patients')
    ax.set_title('Age distribution')
    plt.tight_layout()
    fig.savefig(out_png)
    plt.close(fig)
    return out_png

def np_histogram(ages, bins):
    # simple wrapper to avoid heavy numpy dependency; uses pandas value_counts
    import pandas as pd
    s = pd.Series(ages)
    labels = []
    counts = []
    edges = list(bins)
    for i in range(len(bins)-1):
        lo, hi = bins[i], bins[i+1]
        c = s[(s >= lo) & (s < hi)].count()
        counts.append(int(c))
    return counts, edges

def generate_pdf_report(df, pdf_path='report.pdf'):
    # Generates a PDF with a table summary and an embedded chart
    if df is None:
        raise ValueError('df must be a pandas DataFrame')
    tmp_png = 'tmp_chart.png'
    try:
        generate_patient_chart(df, out_png=tmp_png)
    except Exception:
        # fallback: create a tiny placeholder image
        fig, ax = plt.subplots(figsize=(6,3))
        ax.text(0.5,0.5,'No chart available', ha='center', va='center')
        fig.savefig(tmp_png)
        plt.close(fig)

    c = canvas.Canvas(pdf_path, pagesize=A4)
    width, height = A4
    c.setFont('Helvetica-Bold', 14)
    c.drawString(40, height-40, 'Patient Management Report')
    c.setFont('Helvetica', 10)

    # write a short table summary
    txt = dataframe_summary(df)
    text_obj = c.beginText(40, height-80)
    for line in txt.splitlines():
        text_obj.textLine(line[:90])
    c.drawText(text_obj)

    # insert chart
    img = ImageReader(tmp_png)
    c.drawImage(img, 40, height-350, width=500, preserveAspectRatio=True, mask='auto')
    c.showPage()
    c.save()
    return pdf_path

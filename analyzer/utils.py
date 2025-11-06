# analyzer/utils.py
# General utility functions used in the app

import streamlit as st
import pandas as pd


def show_overview(df):
    """
    Displays high-level overview of the dataset including
    shape and a preview.
    """
    st.subheader("🔍 Dataset Overview")
    st.write("Shape:", df.shape)
    st.write(df.sample(min(len(df), 50)))


def show_column_info(df):
    """
    Displays column data types and missing value summary using styled dataframes.
    """
    st.subheader("📋 Column Info")

    # ----- Data Types -----
    st.markdown("**Data Types:**")
    types_df = pd.DataFrame(
        {"Column": df.columns, "Type": df.dtypes.astype(str).values}
    )
    st.dataframe(types_df, use_container_width=True)

    # ----- Missing Values -----
    missing = df.isnull().sum()
    missing = missing[missing > 0]

    if not missing.empty:
        st.markdown("**Missing Values:**")
        missing_df = pd.DataFrame(
            {
                "Column": missing.index,
                "Missing": missing.values,
                "%": ((missing / len(df)) * 100).round(1),
            }
        ).reset_index(drop=True)

        st.dataframe(
            missing_df.style.format({"Missing": "{:,.0f}", "%": "{:.1f}"})
            .set_properties(**{"text-align": "right"})
            .set_table_styles([{"selector": "th", "props": [("text-align", "left")]}]),
            use_container_width=True,
        )
    else:
        st.success("✅ No missing values found.")


from fpdf import FPDF
from io import BytesIO
from PIL import Image
import matplotlib.pyplot as plt
import tempfile
from bs4 import BeautifulSoup


def export_full_report_to_pdf(df, summary_html, stats_df, chart_figs):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    # Title
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, "Smart CSV Analyzer Report", ln=True)

    # Basic Info
    pdf.set_font("Arial", "", 12)
    shape_str = f"Rows: {df.shape[0]:,}    Columns: {df.shape[1]:,}"
    pdf.cell(0, 10, shape_str[:100], ln=True)

    # Smart Summary Text (plain, no emojis, no lists)
    pdf.set_font("Arial", "", 10)
    pdf.ln(5)
    pdf.cell(0, 10, "Data Summary:", ln=True)

    soup = BeautifulSoup(summary_html, "html.parser")
    for li in soup.find_all("li"):
        text = li.get_text().replace("•", "-")
        text = text.encode("latin-1", "ignore").decode("latin-1")
        pdf.cell(0, 8, f"- {text[:100]}", ln=True)  # truncate each line

    # Descriptive Stats
    pdf.add_page()
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, "Descriptive Statistics", ln=True)

    pdf.set_font("Arial", "", 9)
    stats_df = stats_df.iloc[:, :6]  # Max 6 columns
    col_width = (pdf.w - 20) / len(stats_df.columns)

    # Header
    for col in stats_df.columns:
        safe_col = str(col)[:15]
        pdf.cell(col_width, 8, safe_col, border=1)
    pdf.ln()

    # Rows
    for _, row in stats_df.iterrows():
        for col in stats_df.columns:
            val = str(row[col])[:15]
            val = val.encode("latin-1", "ignore").decode("latin-1")
            pdf.cell(col_width, 8, val, border=1)
        pdf.ln()

    # Charts
    for fig in chart_figs:
        try:
            buf = BytesIO()
            fig.savefig(buf, format="png", dpi=120, bbox_inches="tight")
            buf.seek(0)
            img = Image.open(buf)

            with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp_file:
                img.save(tmp_file.name)
                pdf.add_page()
                pdf.image(tmp_file.name, x=10, y=20, w=180)
            plt.close(fig)
        except Exception as e:
            print("Chart export error:", e)
            continue

    output = BytesIO()
    output.write(
        pdf.output(dest="S").encode("latin-1", "ignore")
        if isinstance(pdf.output(dest="S"), str)
        else pdf.output(dest="S")
    )

    output.seek(0)
    return output

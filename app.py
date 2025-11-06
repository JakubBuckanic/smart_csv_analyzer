# app.py
# Main entry point for the Smart CSV Analyzer web app

import streamlit as st
import pandas as pd
from analyzer.utils import show_overview, show_column_info
from analyzer.charts import (
    show_numeric_charts,
    show_text_charts,
    generate_custom_chart,
    render_chart_with_download,
    plot_bar_chart_export,
    plot_histogram_export,
)
from analyzer.styling import apply_global_style, get_accent_color
from analyzer.summary import generate_summary, render_descriptive_stats

from analyzer.utils import export_full_report_to_pdf


# --------------------------
# Setup and theme
# --------------------------
st.set_page_config(page_title="Smart CSV/Excel Analyzer", layout="wide")
apply_global_style()

st.markdown(
    "<h1 style='color:#4F8EF7;'>Smart CSV/Excel Analyzer</h1>", unsafe_allow_html=True
)
st.markdown(
    "<p style='color:#666;'>Upload your CSV or Excel file and instantly get data insights and visualizations.</p>",
    unsafe_allow_html=True,
)

# --------------------------
# File Upload + Theme
# --------------------------
accent_color = get_accent_color()
uploaded_file = st.file_uploader(
    "Upload a CSV or Excel file", type=["csv", "xlsx", "xls"]
)

# --------------------------
# If CSV is uploaded
# --------------------------
df = None
if uploaded_file is not None:
    try:
        if uploaded_file.name.endswith(".csv"):
            df = pd.read_csv(uploaded_file)
        else:
            excel_file = pd.ExcelFile(uploaded_file)
            sheet_name = st.selectbox("Select a sheet:", excel_file.sheet_names)
            df = excel_file.parse(sheet_name)

        st.success("✅ File uploaded successfully!")

    except Exception as e:
        st.error(f"❌ Error reading file: {e}")
        st.stop()

if df is not None:
    tab1, tab2 = st.tabs(["📊 Overview", "📈 Custom Chart"])

    # --- Tab 1: Overview ---
    with tab1:
        show_overview(df)
        show_column_info(df)

        st.markdown(generate_summary(df), unsafe_allow_html=True)

        st.markdown("### 📊 Descriptive Stats")
        numeric_df = df.select_dtypes(include="number")
        if numeric_df.empty:
            st.info("No numeric columns to describe.")
        else:
            st.dataframe(
                render_descriptive_stats(numeric_df),
                use_container_width=True,
            )

        st.markdown("### 📊 Distribution of Numerical Columns")
        show_numeric_charts(df, accent_color)
        st.markdown("### 📊 Distribution of Categorical Columns")
        show_text_charts(df, accent_color)
        st.markdown("### 📄 Export Full Report to PDF")
        if st.button("📥 Export Summary + Stats + Charts to PDF"):
            # --- Collect charts the user selected ---
            chart_figs = []

            # Get selected columns from Streamlit session state
            selected_numeric = st.session_state.get("num_cols", [])
            selected_text = st.session_state.get("cat_cols", [])
            for col in selected_numeric:
                fig = plot_histogram_export(df, col, accent_color)
                chart_figs.append(fig)

            for col in selected_text:
                fig = plot_bar_chart_export(df, col, accent_color)
                chart_figs.append(fig)

            # Add last custom chart if created
            if "last_custom_chart" in st.session_state:
                chart_figs.append(st.session_state["last_custom_chart"])

            # Prepare content
            stats_df = render_descriptive_stats(df.select_dtypes(include="number"))
            summary_html = generate_summary(df)

            # Generate PDF
            pdf_file = export_full_report_to_pdf(df, summary_html, stats_df, chart_figs)
            st.download_button(
                "⬇️ Download PDF", data=pdf_file, file_name="smart_csv_report.pdf"
            )

    # --- Tab 2: Custom Chart ---
    with tab2:
        st.markdown("### 🎨 Custom Chart Builder")

        chart_type = st.selectbox("Chart Type", ["Line", "Bar", "Scatter"])
        x_col = st.selectbox("X-axis Column", df.columns)
        y_col = st.selectbox("Y-axis Column", df.columns)

        agg_method = "None"
        horizontal_bar = False

        if chart_type in ["Bar", "Line"]:
            if not pd.api.types.is_numeric_dtype(df[y_col]):
                st.warning("Y column must be numeric for this chart type.")
            else:
                agg_method = st.selectbox(
                    "Aggregation method for Y values:", ["Mean", "Sum", "Count"]
                )

        chart_title = st.text_input("Chart Title", f"{y_col} by {x_col}")
        x_label = st.text_input("X-axis Label", x_col)
        y_label = st.text_input("Y-axis Label", y_col)

        # Optional threshold
        st.markdown("### ⚙️ Threshold Line (optional)")
        add_threshold = st.checkbox("Add a threshold line")
        threshold_axis = None
        threshold_value = None
        threshold_color = "#FF4B4B"
        threshold_label = ""

        if add_threshold:
            threshold_axis = st.radio(
                "Apply to:", ["X-axis", "Y-axis"], horizontal=True
            )
            threshold_value = st.number_input("Threshold value", step=1.0)
            threshold_color = st.color_picker("Line color", threshold_color)
            threshold_label = st.text_input("Threshold Label (optional)", "")

        if st.button("Generate Chart"):
            fig = generate_custom_chart(
                df,
                x_col,
                y_col,
                chart_type=chart_type,
                title=chart_title,
                x_label=x_label,
                y_label=y_label,
                accent_color=accent_color,
                threshold_enabled=add_threshold,
                threshold_axis=threshold_axis,
                threshold_value=threshold_value,
                threshold_color=threshold_color,
                agg_method=agg_method,
                horizontal_bar=horizontal_bar,
                threshold_label=threshold_label,
            )
            if fig is not None:
                render_chart_with_download(
                    fig, filename=f"{chart_title or 'custom_chart'}.png"
                )
                st.session_state["last_custom_chart"] = fig  # Save chart for report

else:
    st.info("📂 Please upload a CSV or Excel file to begin.")

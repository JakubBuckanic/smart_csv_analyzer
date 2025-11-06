import pandas as pd


import pandas as pd
import textwrap

import streamlit as st
import io
from PIL import Image


def generate_summary(df):
    n_rows, n_cols = df.shape
    numeric_cols = df.select_dtypes(include="number").columns.tolist()
    text_cols = df.select_dtypes(exclude="number").columns.tolist()

    html = """
<div style='line-height:1.8; font-size:16px;'>
  <h3>🧠 <b>Smart Data Insights</b></h3>

  <p style='margin-left: 15px;'>
    📄 <b>Shape:</b> {} rows × {} columns<br>
    🔢 <b>Numeric columns ({}):</b> {}<br>
    🔤 <b>Text columns ({}):</b> {}
  </p>

  <h4 style='margin-top:10px;'>📌 Insights:</h4>
  <ul style='margin-left: 30px;'>
""".format(
        f"{n_rows:,}",
        n_cols,
        len(numeric_cols),
        ", ".join(numeric_cols) or "None",
        len(text_cols),
        ", ".join(text_cols) or "None",
    )

    # Missing values
    missing = df.isnull().sum()
    total_missing = missing[missing > 0]
    if not total_missing.empty:
        for col, count in total_missing.items():
            percent = (count / n_rows * 100) if n_rows > 0 else 0
            html += f"<li><b>{col}</b> has {percent:.1f}% missing values ({count:,} rows).</li>"
    else:
        html += "<li>No missing values detected.</li>"

    # Numeric insights
    for col in numeric_cols:
        col_data = df[col].dropna()
        if col_data.empty:
            continue
        mean = col_data.mean()
        min_val = col_data.min()
        max_val = col_data.max()
        std = col_data.std()
        skew = col_data.skew()
        skew_label = (
            "right-skewed"
            if skew > 1
            else "left-skewed" if skew < -1 else "fairly symmetrical"
        )
        html += (
            f"<li><b>{col}</b> ranges from {min_val:.1f} to {max_val:.1f}, "
            f"mean = {mean:.1f}, std = {std:.1f} ({skew_label}).</li>"
        )

    # Text insights
    for col in text_cols:
        non_null = df[col].dropna()
        if non_null.empty:
            continue
        top_val = non_null.mode().iloc[0]
        freq = non_null.value_counts().iloc[0]
        percent = (freq / len(non_null)) * 100
        html += (
            f"<li><b>{col}</b>: Most frequent value is <i>'{top_val}'</i> "
            f"({percent:.1f}% of non-missing records).</li>"
        )

    # Outliers
    for col in numeric_cols:
        col_data = df[col].dropna()
        if col_data.empty:
            continue
        Q1 = col_data.quantile(0.25)
        Q3 = col_data.quantile(0.75)
        IQR = Q3 - Q1
        lower = Q1 - 1.5 * IQR
        upper = Q3 + 1.5 * IQR
        outliers = col_data[(col_data < lower) | (col_data > upper)]
        count = len(outliers)
        percent = (count / len(col_data)) * 100

        if count == 0:
            html += f"<li><b>{col}</b> has no significant outliers based on the IQR method.</li>"
        else:
            direction = []
            if (col_data > upper).any():
                direction.append("high")
            if (col_data < lower).any():
                direction.append("low")
            dir_text = " and ".join(direction)
            html += (
                f"<li><b>{col}</b> has {count} outlier{'s' if count > 1 else ''} "
                f"({percent:.1f}%) on the {dir_text} end of the distribution.</li>"
            )

    html += "</ul></div>"
    return html


def render_descriptive_stats(df):
    desc = df.describe().T.reset_index().rename(columns={"index": "Column"})
    desc = desc.rename(
        columns={
            "count": "Count",
            "mean": "Mean",
            "min": "Min",
            "25%": "25%",
            "50%": "Median",
            "75%": "75%",
            "max": "Max",
            "std": "Std",
        }
    )
    desc = desc[
        ["Column", "Count", "Mean", "Min", "25%", "Median", "75%", "Max", "Std"]
    ]

    for col in desc.columns[1:]:
        desc[col] = desc[col].apply(
            lambda x: f"{x:.2f}".rstrip("0").rstrip(".") if pd.notnull(x) else x
        )

    return desc

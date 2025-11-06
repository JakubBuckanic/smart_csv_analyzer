import matplotlib.pyplot as plt
import numpy as np
import streamlit as st
import base64
import io


COLOR_TEXT = "#333333"


def render_chart_with_download(fig, filename="chart.png"):
    """Displays a chart and a styled download button with white background."""
    # Save the chart to a bytes buffer
    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight", dpi=300)
    buf.seek(0)

    # Show the chart
    st.pyplot(fig)

    # Convert buffer to base64 string
    b64 = base64.b64encode(buf.read()).decode()

    # Styled download button (white background)
    button_html = f"""
        <a href="data:image/png;base64,{b64}" download="{filename}">
            <div style="
                display: inline-block;
                padding: 0.5em 1.2em;
                margin-top: 12px;
                background-color: #fff;
                border: 1px solid #ccc;
                color: #333;
                border-radius: 6px;
                text-decoration: none;
                font-weight: 500;
                font-size: 14px;
                box-shadow: 1px 1px 3px rgba(0,0,0,0.08);
            ">
                📥 Download as PNG
            </div>
        </a>
    """
    st.markdown(button_html, unsafe_allow_html=True)


def plot_histogram(df, column, accent_color):
    data = df[column].dropna()
    counts, bins = np.histogram(data, bins=20)

    with st.expander(f"Customize '{column}' Distribution Chart"):
        chart_title = st.text_input(
            f"Title for '{column}' distribution", f"{column} Distribution"
        )
        x_label = st.text_input(f"X-axis Label for '{column}'", column)
        y_label = st.text_input(f"Y-axis Label for '{column}'", "Count")

    fig, ax = plt.subplots(figsize=(6, 4))
    bar_width = bins[1] - bins[0]
    for i in range(len(counts)):
        left = bins[i]
        height = counts[i]
        bar = plt.Rectangle(
            (left, 0),
            bar_width,
            height,
            facecolor=accent_color,
            edgecolor="white",
            linewidth=0.5,
        )
        ax.add_patch(bar)

    ylim_max = max(counts) * 1.1 if max(counts) > 0 else 1
    ax.set_xlim([bins[0], bins[-1]])
    ax.set_ylim(0, ylim_max)
    _style_axes(ax, x_label, y_label, chart_title)
    fig.tight_layout()
    return fig


def plot_bar_chart(df, column, accent_color):
    value_counts = df[column].value_counts().head(10)

    with st.expander(f"Customize '{column}' Bar Chart"):
        chart_title = st.text_input(
            f"Title for '{column}' categories", f"{column} Top 10 Categories"
        )
        x_label = st.text_input(f"X-axis Label for '{column}'", column)
        y_label = st.text_input(f"Y-axis Label for '{column}'", "Count")

    fig, ax = plt.subplots(figsize=(6, 4))
    value_counts.plot(kind="bar", ax=ax, color=accent_color, edgecolor="white")

    ylim_max = value_counts.max() * 1.1 if value_counts.max() > 0 else 1
    ax.set_ylim(0, ylim_max)

    _style_axes(ax, x_label, y_label, chart_title)
    ax.tick_params(axis="x", labelrotation=45)
    fig.tight_layout()
    return fig


def show_numeric_charts(df, accent_color):
    numeric_cols = df.select_dtypes(include="number").columns
    selected_cols = st.multiselect(
        "Select numeric columns to display:", list(numeric_cols), key="num_cols"
    )

    if selected_cols:
        cols = st.columns(2)
        for i, col in enumerate(selected_cols):
            with cols[i % 2]:
                fig = plot_histogram(df, col, accent_color)
                render_chart_with_download(fig, filename=f"{col}_distribution.png")
                plt.close(fig)


def show_text_charts(df, accent_color):
    text_cols = df.select_dtypes(exclude="number").columns
    selected_cols = st.multiselect(
        "Select categorical columns to display:", list(text_cols), key="cat_cols"
    )

    if selected_cols:
        cols = st.columns(2)
        for i, col in enumerate(selected_cols):
            with cols[i % 2]:
                fig = plot_bar_chart(df, col, accent_color)
                render_chart_with_download(fig, filename=f"{col}_categories.png")
                plt.close(fig)


def generate_custom_chart(
    df,
    x_col,
    y_col,
    chart_type,
    title,
    x_label,
    y_label,
    accent_color,
    threshold_enabled=False,
    threshold_axis=None,
    threshold_value=None,
    threshold_color="#FF4B4B",
    agg_method="None",
    horizontal_bar=False,
    threshold_label=None,
):
    fig, ax = plt.subplots(figsize=(6, 4))

    if chart_type == "Bar":
        if not np.issubdtype(df[y_col].dtype, np.number):
            st.warning(f"Column '{y_col}' must be numeric for aggregation.")
            return None

        df_grouped = _aggregate_data(df, x_col, y_col, agg_method)
        if df_grouped is None:
            return None
        y_col_final = df_grouped.columns[1]  # Aggregated column

        y_max = df_grouped[y_col_final].max()
        y_max = y_max if y_max > 0 else 1

        if horizontal_bar:
            ax.barh(
                df_grouped[x_col],
                df_grouped[y_col_final],
                color=accent_color,
                edgecolor="white",
            )
            ax.set_xlim(0, y_max * 1.1)
            _style_axes(ax, y_label, x_label, title)
        else:
            ax.bar(
                df_grouped[x_col],
                df_grouped[y_col_final],
                color=accent_color,
                edgecolor="white",
            )
            ax.set_ylim(0, y_max * 1.1)
            ax.tick_params(axis="x", labelrotation=45)
            _style_axes(ax, x_label, y_label, title)

    elif chart_type in ["Line", "Scatter"]:
        if not np.issubdtype(df[x_col].dtype, np.number) or not np.issubdtype(
            df[y_col].dtype, np.number
        ):
            st.warning("Both X and Y columns must be numeric for this chart type.")
            return None

        df_grouped = (
            _aggregate_data(df, x_col, y_col, "Mean") if chart_type == "Line" else df
        )

        if df_grouped is None:
            return None

        if chart_type == "Line":
            ax.plot(
                df_grouped[x_col], df_grouped[y_col], color=accent_color, linewidth=2
            )
        else:
            ax.scatter(
                df_grouped[x_col],
                df_grouped[y_col],
                color=accent_color,
                edgecolor="white",
            )

        _style_axes(ax, x_label, y_label, title)

    if threshold_enabled and threshold_value is not None:
        if threshold_axis == "Y-axis":
            ax.axhline(
                y=threshold_value,
                color=threshold_color,
                linestyle="--",
                linewidth=2,
                label=threshold_label,
            )
        elif threshold_axis == "X-axis":
            ax.axvline(
                x=threshold_value,
                color=threshold_color,
                linestyle="--",
                linewidth=2,
                label=threshold_label,
            )

        if threshold_label:
            ax.legend()

    fig.tight_layout()
    return fig


def _style_axes(ax, x_label, y_label, title=None):
    if title:
        ax.set_title(title, fontsize=14, fontweight="bold", color=COLOR_TEXT)
    ax.set_xlabel(x_label, fontsize=11)
    ax.set_ylabel(y_label, fontsize=11)
    ax.tick_params(axis="x", labelsize=9)
    ax.tick_params(axis="y", labelsize=9)
    ax.grid(False)
    ax.set_facecolor("white")


def _aggregate_data(df, x_col, y_col, method):
    try:
        if method == "Mean":
            return df.groupby(x_col, as_index=False)[y_col].mean()
        elif method == "Sum":
            return df.groupby(x_col, as_index=False)[y_col].sum()
        elif method == "Count":
            result = df.groupby(x_col, as_index=False)[y_col].count()
            result.rename(columns={y_col: "Count"}, inplace=True)
            return result
        else:
            return df[[x_col, y_col]]
    except Exception as e:
        st.error(f"❌ Error aggregating data: {e}")
        return None


# EXPORT
# For export only – no Streamlit widgets
def plot_histogram_export(df, column, accent_color):
    data = df[column].dropna()
    counts, bins = np.histogram(data, bins=20)

    fig, ax = plt.subplots(figsize=(6, 4))
    bar_width = bins[1] - bins[0]
    for i in range(len(counts)):
        left = bins[i]
        height = counts[i]
        bar = plt.Rectangle(
            (left, 0),
            bar_width,
            height,
            facecolor=accent_color,
            edgecolor="white",
            linewidth=0.5,
        )
        ax.add_patch(bar)

    ax.set_xlim([bins[0], bins[-1]])
    ax.set_ylim(0, max(counts) * 1.1 if max(counts) > 0 else 1)
    ax.set_title(f"{column} Distribution")
    ax.set_xlabel(column)
    ax.set_ylabel("Count")
    fig.tight_layout()
    return fig


def plot_bar_chart_export(df, column, accent_color):
    value_counts = df[column].value_counts().head(10)
    fig, ax = plt.subplots(figsize=(6, 4))
    value_counts.plot(kind="bar", ax=ax, color=accent_color, edgecolor="white")

    ax.set_title(f"{column} Top 10 Categories")
    ax.set_xlabel(column)
    ax.set_ylabel("Count")
    ax.tick_params(axis="x", labelrotation=45)
    ax.set_ylim(0, value_counts.max() * 1.1 if value_counts.max() > 0 else 1)
    fig.tight_layout()
    return fig

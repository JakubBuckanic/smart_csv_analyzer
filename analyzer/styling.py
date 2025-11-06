# analyzer/styling.py
# Theme and styling tools for Streamlit app

import streamlit as st

# Default pastel options
PASTEL_COLORS = {
    "Sky Blue": "#A3C9F9",
    "Mint Green": "#A7E9AF",
    "Peach": "#FFBCB3",
    "Lavender": "#D5B3FF",
    "Soft Gray": "#D3D3D3",
}


def apply_global_style():
    """Injects custom CSS into Streamlit app for consistent theming."""
    st.markdown(
        """
        <style>
            body {
                background-color: #FAFAFA;
                color: #333333;
                font-family: 'Segoe UI', sans-serif;
            }
            .stButton>button {
                background-color: #4F8EF7;
                color: white;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


def get_accent_color():
    """Inline widget for picking chart accent color (no sidebar)."""
    with st.expander("🎨 Style Options", expanded=False):
        st.caption("Customize the accent color for your charts.")
        col1, col2 = st.columns(2)
        with col1:
            preset_name = st.selectbox(
                "Choose preset color",
                list(PASTEL_COLORS.keys()),
                key="preset_color",
            )
        with col2:
            custom_color = st.color_picker("Custom color", PASTEL_COLORS[preset_name])

    return custom_color

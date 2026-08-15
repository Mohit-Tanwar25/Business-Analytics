"""
Theme injection and modern Plotly chart styling
"""

DARK_COLOR_SEQUENCE = [
    "#38bdf8",  # Sky Blue
    "#818cf8",  # Indigo
    "#34d399",  # Emerald
    "#f472b6",  # Pink / Rose
    "#fbbf24",  # Amber
    "#a78bfa",  # Violet
    "#2dd4bf",  # Teal
]

LIGHT_COLOR_SEQUENCE = [
    "#0284c7",  # Sky
    "#4f46e5",  # Indigo
    "#059669",  # Emerald
    "#e11d48",  # Rose
    "#d97706",  # Amber
    "#7c3aed",  # Violet
    "#0d9488",  # Teal
]


def get_theme_css(dark_mode: bool) -> str:
    """Generate dynamic CSS rules that apply synchronously based on dark_mode boolean."""
    if dark_mode:
        return """
        /* ---------------- DARK MODE STYLES ---------------- */
        .stApp {
            background: radial-gradient(circle at 15% 10%, rgba(37, 99, 235, 0.12) 0%, transparent 40%),
                        radial-gradient(circle at 85% 85%, rgba(124, 58, 237, 0.10) 0%, transparent 40%),
                        linear-gradient(180deg, #090d16 0%, #0d1322 50%, #070a12 100%) !important;
            color: #f1f5f9 !important;
        }

        .stApp h1, .stApp h2, .stApp h3, .stApp h4, .stApp h5, .stApp h6,
        .stApp p, .stApp span, .stApp label, .stApp div,
        .stApp [data-testid="stMarkdownContainer"] p {
            color: #f1f5f9;
        }

        section[data-testid="stSidebar"] {
            background: linear-gradient(180deg, #090d16 0%, #0d1322 100%) !important;
            border-right: 1px solid rgba(255, 255, 255, 0.08) !important;
        }

        section[data-testid="stSidebar"] h1,
        section[data-testid="stSidebar"] h2,
        section[data-testid="stSidebar"] h3,
        section[data-testid="stSidebar"] p,
        section[data-testid="stSidebar"] label,
        section[data-testid="stSidebar"] span {
            color: #f1f5f9;
        }

        .sidebar-logo-text {
            color: #ffffff !important;
        }

        .sidebar-section-label {
            color: #64748b !important;
        }

        .dashboard-header {
            background: rgba(15, 23, 42, 0.65) !important;
            border: 1px solid rgba(255, 255, 255, 0.08) !important;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3) !important;
        }

        .dashboard-title-text {
            color: #ffffff !important;
        }

        .kpi-card {
            background: rgba(15, 23, 42, 0.7) !important;
            border: 1px solid rgba(255, 255, 255, 0.08) !important;
            box-shadow: 0 8px 24px rgba(0, 0, 0, 0.25) !important;
            backdrop-filter: blur(14px) !important;
        }

        .kpi-title {
            color: #94a3b8 !important;
        }

        .kpi-value {
            color: #ffffff !important;
        }

        .kpi-icon {
            background: rgba(30, 41, 59, 0.8) !important;
        }

        .feature-card {
            background: rgba(15, 23, 42, 0.65) !important;
            border: 1px solid rgba(255, 255, 255, 0.08) !important;
        }

        .feature-title {
            color: #ffffff !important;
        }

        .feature-desc {
            color: #94a3b8 !important;
        }

        .hero-badge {
            background: rgba(30, 41, 59, 0.7) !important;
            color: #38bdf8 !important;
            border: 1px solid rgba(56, 189, 248, 0.3) !important;
        }

        .gradient-title {
            background: linear-gradient(135deg, #38bdf8 0%, #818cf8 50%, #c084fc 100%) !important;
            -webkit-background-clip: text !important;
            -webkit-text-fill-color: transparent !important;
        }

        .hero-subtitle {
            color: #94a3b8 !important;
        }

        [data-testid="stVerticalBlock"] > div[data-testid="stVerticalBlockBorderWrapper"] {
            background: rgba(15, 23, 42, 0.6) !important;
            border: 1px solid rgba(255, 255, 255, 0.07) !important;
            box-shadow: 0 8px 24px rgba(0, 0, 0, 0.25) !important;
        }

        .chart-title {
            color: #f1f5f9 !important;
        }

        .stTabs [data-baseweb="tab"] {
            background: rgba(30, 41, 59, 0.5) !important;
            color: #94a3b8 !important;
            border-color: rgba(255, 255, 255, 0.05) !important;
        }

        .stTabs [data-baseweb="tab"]:hover {
            background: rgba(30, 41, 59, 0.8) !important;
            color: #f1f5f9 !important;
        }

        .stTabs [aria-selected="true"] {
            background: linear-gradient(135deg, #2563eb, #4f46e5) !important;
            color: #ffffff !important;
            box-shadow: 0 4px 16px rgba(37, 99, 235, 0.35) !important;
        }

        [data-testid="stFileUploader"] {
            background: rgba(15, 23, 42, 0.6) !important;
            border: 2px dashed rgba(99, 102, 241, 0.35) !important;
        }

        [data-baseweb="select"] > div, [data-baseweb="input"] {
            background-color: #1e293b !important;
            color: #f8fafc !important;
            border-color: #334155 !important;
        }

        [data-testid="stExpander"] details {
            background: rgba(15, 23, 42, 0.6) !important;
            border: 1px solid rgba(255, 255, 255, 0.08) !important;
        }

        .header-pill {
            background: rgba(30, 41, 59, 0.8) !important;
            color: #cbd5e1 !important;
            border: 1px solid rgba(255, 255, 255, 0.06) !important;
        }

        .insight-text {
            color: #f1f5f9 !important;
        }

        [data-testid="collapsedControl"] {
            background: rgba(30, 41, 59, 0.85) !important;
            border: 1px solid rgba(255, 255, 255, 0.15) !important;
            color: #ffffff !important;
        }
        """
    else:
        return """
        /* ---------------- HIGH-CONTRAST LIGHT MODE STYLES ---------------- */
        .stApp {
            background: radial-gradient(circle at 10% 10%, rgba(99, 102, 241, 0.06) 0%, transparent 40%),
                        radial-gradient(circle at 90% 90%, rgba(14, 165, 233, 0.06) 0%, transparent 40%),
                        linear-gradient(180deg, #f8fafc 0%, #f1f5f9 50%, #e2e8f0 100%) !important;
            color: #0f172a !important;
        }

        /* Headings and text in high-contrast deep black/charcoal */
        .stApp h1, .stApp h2, .stApp h3, .stApp h4, .stApp h5, .stApp h6,
        .stApp label, .stApp [data-testid="stMarkdownContainer"] p,
        .stApp [data-testid="stMarkdownContainer"] li,
        .stApp [data-testid="stMarkdownContainer"] span {
            color: #0f172a !important;
            font-weight: 600;
        }

        .stApp p {
            color: #1e293b !important;
        }

        .stCaption, [data-testid="stCaptionContainer"] {
            color: #334155 !important;
            font-weight: 500 !important;
        }

        section[data-testid="stSidebar"] {
            background: linear-gradient(180deg, #ffffff 0%, #f8fafc 100%) !important;
            border-right: 1px solid #e2e8f0 !important;
        }

        section[data-testid="stSidebar"] h1,
        section[data-testid="stSidebar"] h2,
        section[data-testid="stSidebar"] h3,
        section[data-testid="stSidebar"] p,
        section[data-testid="stSidebar"] label,
        section[data-testid="stSidebar"] span,
        section[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] {
            color: #0f172a !important;
        }

        .sidebar-logo-text {
            color: #0f172a !important;
            font-weight: 800 !important;
        }

        .sidebar-section-label {
            color: #475569 !important;
            font-weight: 700 !important;
        }

        .dashboard-header {
            background: #ffffff !important;
            border: 1px solid #cbd5e1 !important;
            box-shadow: 0 4px 16px rgba(0, 0, 0, 0.05) !important;
        }

        .dashboard-title-text {
            color: #0f172a !important;
            font-weight: 800 !important;
        }

        .kpi-card {
            background: #ffffff !important;
            border: 1px solid #cbd5e1 !important;
            box-shadow: 0 4px 14px rgba(0, 0, 0, 0.04) !important;
        }

        .kpi-title {
            color: #334155 !important;
            font-weight: 700 !important;
        }

        .kpi-value {
            color: #0f172a !important;
            font-weight: 800 !important;
        }

        .kpi-subtext {
            color: #475569 !important;
            font-weight: 600 !important;
        }

        .kpi-icon {
            background: #f1f5f9 !important;
            border: 1px solid #e2e8f0 !important;
        }

        .feature-card {
            background: #ffffff !important;
            border: 1px solid #cbd5e1 !important;
            box-shadow: 0 4px 14px rgba(0, 0, 0, 0.04) !important;
        }

        .feature-title {
            color: #0f172a !important;
            font-weight: 700 !important;
        }

        .feature-desc {
            color: #334155 !important;
            font-weight: 500 !important;
        }

        .hero-badge {
            background: #ffffff !important;
            color: #0369a1 !important;
            border: 1px solid #7dd3fc !important;
            box-shadow: 0 2px 10px rgba(3, 105, 161, 0.1) !important;
        }

        .gradient-title {
            background: linear-gradient(135deg, #0369a1 0%, #4338ca 50%, #6d28d9 100%) !important;
            -webkit-background-clip: text !important;
            -webkit-text-fill-color: transparent !important;
        }

        .hero-subtitle {
            color: #1e293b !important;
            font-weight: 500 !important;
        }

        [data-testid="stVerticalBlock"] > div[data-testid="stVerticalBlockBorderWrapper"] {
            background: #ffffff !important;
            border: 1px solid #cbd5e1 !important;
            box-shadow: 0 4px 14px rgba(0, 0, 0, 0.04) !important;
        }

        .chart-title {
            color: #0f172a !important;
            font-weight: 700 !important;
        }

        .stTabs [data-baseweb="tab"] {
            background: #f1f5f9 !important;
            color: #334155 !important;
            border-color: #cbd5e1 !important;
            font-weight: 600 !important;
        }

        .stTabs [data-baseweb="tab"]:hover {
            color: #0f172a !important;
            background: #e2e8f0 !important;
        }

        .stTabs [aria-selected="true"] {
            background: #2563eb !important;
            color: #ffffff !important;
            box-shadow: 0 4px 14px rgba(37, 99, 235, 0.3) !important;
        }

        .stTabs [aria-selected="true"] * {
            color: #ffffff !important;
        }

        [data-testid="stFileUploader"] {
            background: #ffffff !important;
            border: 2px dashed #94a3b8 !important;
        }

        [data-testid="stFileUploader"] * {
            color: #0f172a !important;
        }

        [data-baseweb="select"] > div, [data-baseweb="input"] {
            background-color: #ffffff !important;
            color: #0f172a !important;
            border-color: #94a3b8 !important;
        }

        [data-baseweb="select"] * {
            color: #0f172a !important;
        }

        [data-testid="stExpander"] details {
            background: #ffffff !important;
            border: 1px solid #cbd5e1 !important;
        }

        [data-testid="stExpander"] summary * {
            color: #0f172a !important;
            font-weight: 600 !important;
        }

        .header-pill {
            background: #f1f5f9 !important;
            color: #0f172a !important;
            border: 1px solid #cbd5e1 !important;
            font-weight: 600 !important;
        }

        .header-pill.accent {
            background: #e0f2fe !important;
            color: #0369a1 !important;
            border: 1px solid #7dd3fc !important;
        }

        .insight-text {
            color: #0f172a !important;
            font-weight: 600 !important;
        }

        .insight-card.success {
            background: #ecfdf5 !important;
            border: 1px solid #a7f3d0 !important;
        }

        .insight-card.info {
            background: #f0f9ff !important;
            border: 1px solid #bae6fd !important;
        }

        .insight-card.warning {
            background: #fffbeb !important;
            border: 1px solid #fde68a !important;
        }

        .insight-card.danger {
            background: #fef2f2 !important;
            border: 1px solid #fecaca !important;
        }

        [data-testid="collapsedControl"] {
            background: #ffffff !important;
            border: 1px solid #94a3b8 !important;
            color: #0f172a !important;
            box-shadow: 0 4px 14px rgba(0, 0, 0, 0.08) !important;
        }

        [data-testid="stDataFrame"] * {
            color: #0f172a !important;
        }
        """


def inject_theme(dark_mode: bool) -> None:
    """Load CSS and apply the active theme rules synchronously."""
    import streamlit as st

    theme_css = get_theme_css(dark_mode)

    try:
        with open("style.css", encoding="utf-8") as f:
            base_css = f.read()
    except Exception:
        base_css = ""

    st.markdown(
        f"<style>\n{base_css}\n{theme_css}\n</style>",
        unsafe_allow_html=True,
    )


def apply_chart_theme(fig, dark_mode: bool):
    """Apply modern typography, smooth grid lines, and rich color palette to Plotly figures."""
    if dark_mode:
        fig.update_layout(
            template="plotly_dark",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(15, 23, 42, 0.4)",
            font=dict(
                family="Plus Jakarta Sans, sans-serif",
                color="#cbd5e1",
                size=12,
            ),
            colorway=DARK_COLOR_SEQUENCE,
            xaxis=dict(
                gridcolor="rgba(255, 255, 255, 0.06)",
                zerolinecolor="rgba(255, 255, 255, 0.1)",
                linecolor="rgba(255, 255, 255, 0.1)",
            ),
            yaxis=dict(
                gridcolor="rgba(255, 255, 255, 0.06)",
                zerolinecolor="rgba(255, 255, 255, 0.1)",
                linecolor="rgba(255, 255, 255, 0.1)",
            ),
            hoverlabel=dict(
                bgcolor="#0f172a",
                font_size=13,
                font_family="Plus Jakarta Sans, sans-serif",
                bordercolor="rgba(255, 255, 255, 0.15)",
            ),
        )
    else:
        fig.update_layout(
            template="plotly_white",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(248, 250, 252, 0.6)",
            font=dict(
                family="Plus Jakarta Sans, sans-serif",
                color="#0f172a",
                size=12,
            ),
            colorway=LIGHT_COLOR_SEQUENCE,
            xaxis=dict(
                gridcolor="rgba(0, 0, 0, 0.08)",
                zerolinecolor="rgba(0, 0, 0, 0.15)",
                linecolor="rgba(0, 0, 0, 0.15)",
                tickfont=dict(color="#0f172a", family="Plus Jakarta Sans, sans-serif"),
                title_font=dict(color="#0f172a", family="Plus Jakarta Sans, sans-serif"),
            ),
            yaxis=dict(
                gridcolor="rgba(0, 0, 0, 0.08)",
                zerolinecolor="rgba(0, 0, 0, 0.15)",
                linecolor="rgba(0, 0, 0, 0.15)",
                tickfont=dict(color="#0f172a", family="Plus Jakarta Sans, sans-serif"),
                title_font=dict(color="#0f172a", family="Plus Jakarta Sans, sans-serif"),
            ),
            hoverlabel=dict(
                bgcolor="#ffffff",
                font_size=13,
                font_family="Plus Jakarta Sans, sans-serif",
                font_color="#0f172a",
                bordercolor="#cbd5e1",
            ),
        )

    return fig

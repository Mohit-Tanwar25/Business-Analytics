import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from analysis import *
from file_storage import (
    count_duplicate_datasets,
    delete_dataset,
    format_uploaded_at,
    get_active_dataset_id,
    get_dataset,
    get_db_info,
    get_last_error,
    init_database_tables,
    list_datasets,
    load_dataset_from_database,
    load_from_database,
    run_dataset_cleanup,
    set_active_dataset,
    storage_stats,
    store_uploaded_csv,
    test_database_connection,
)
from pdf_export import generate_dashboard_pdf
from theme import apply_chart_theme, inject_theme

# ---------------- PAGE CONFIG ----------------

st.set_page_config(
    page_title="Business Intelligence Dashboard",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------- SESSION STATE ----------------

if "uploaded" not in st.session_state:
    st.session_state.uploaded = False

if "active_dataset_id" not in st.session_state:
    st.session_state.active_dataset_id = get_active_dataset_id()

if "db_initialized" not in st.session_state:
    init_database_tables()
    st.session_state.db_initialized = True

if "dark_mode" not in st.session_state:
    st.session_state.dark_mode = True

# ---------------- HELPERS ----------------

def sidebar_section_label(title: str) -> None:
    st.sidebar.markdown(
        f'<div class="sidebar-section-label">{title}</div>',
        unsafe_allow_html=True,
    )


def dataset_option_label(item: dict) -> str:
    """Formatted label for saved dataset dropdowns."""
    short_id = item["id"][:6]
    return (
        f"📁 {item['name']} ({item['rows']:,} rows · {format_uploaded_at(item['uploaded_at'])})"
    )


def process_csv_upload(uploaded_file, source_key: str) -> tuple[str, str | None]:
    """Store CSV once per upload. Returns (status, dataset_id)."""
    file_signature = f"{uploaded_file.name}_{uploaded_file.size}"
    session_key = f"processed_upload_{source_key}"

    if st.session_state.get(session_key) == file_signature:
        return "skipped", None

    dataset_id = store_uploaded_csv(
        uploaded_file.getvalue(),
        uploaded_file.name,
    )

    if not dataset_id:
        return "failed", None

    st.session_state[session_key] = file_signature
    return "success", dataset_id


def process_csv_uploads(uploaded_files, source_prefix: str) -> str:
    """Upload one or more files; activate the last successful dataset."""
    if not isinstance(uploaded_files, list):
        uploaded_files = [uploaded_files]

    last_dataset_id = None
    any_success = False
    any_failed = False
    all_skipped = True

    for uploaded_file in uploaded_files:
        safe_key = f"{source_prefix}_{uploaded_file.name}_{uploaded_file.size}"
        status, dataset_id = process_csv_upload(uploaded_file, safe_key)
        if status == "success" and dataset_id:
            any_success = True
            all_skipped = False
            last_dataset_id = dataset_id
        elif status == "failed":
            any_failed = True
            all_skipped = False
        elif status != "skipped":
            all_skipped = False

    if last_dataset_id and activate_dataset(last_dataset_id):
        return "success"
    if any_failed:
        return "failed"
    if all_skipped:
        return "skipped"
    return "failed"


@st.cache_data(ttl=300, show_spinner=False)
def load_dataset_cached(dataset_id: str) -> pd.DataFrame:
    return load_dataset_from_database(dataset_id)


@st.cache_data(ttl=60, show_spinner=False)
def list_datasets_cached() -> list[dict]:
    return list_datasets()


def activate_dataset(dataset_id: str) -> bool:
    if get_dataset(dataset_id) is None:
        return False

    df = load_dataset_cached(dataset_id)
    if df.empty:
        return False

    set_active_dataset(dataset_id)
    st.session_state.active_dataset_id = dataset_id
    st.session_state.uploaded = True
    return True


def clear_app_cache():
    """Clear memory cache when dataset is added or deleted."""
    load_dataset_cached.clear()
    list_datasets_cached.clear()


@st.cache_data(ttl=120, show_spinner="Generating Executive PDF Report...")
def get_cached_pdf(df_to_export: pd.DataFrame, summary_text: str) -> bytes:
    return generate_dashboard_pdf(df_to_export, summary_text)


# ---------------- SIDEBAR CONTROLS ----------------

# App Branding
st.sidebar.markdown(
    """
    <div class="sidebar-logo">
        <span style="font-size: 1.8rem;">📊</span>
        <div>
            <div class="sidebar-logo-text">PulseAnalytics</div>
            <div style="font-size: 0.75rem; color: #64748b; font-weight: 600;">ENTERPRISE BI PLATFORM</div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# Theme Toggle
dark_mode = st.sidebar.toggle(
    "🌙 Dark Mode",
    value=st.session_state.dark_mode,
    key="dark_mode_toggle",
)
st.session_state.dark_mode = dark_mode
inject_theme(dark_mode)

# Database Connection Status in Sidebar
db_info = get_db_info()
sidebar_section_label("Cloud Database")

if db_info["is_supabase"]:
    st.sidebar.success("🟢 Supabase Connected")
elif db_info["is_local_sqlite"]:
    st.sidebar.info("💾 Local Database (Ready)")
elif db_info["connected"]:
    st.sidebar.success(f"🟢 Connected: {db_info['type']}")
else:
    st.sidebar.error("🔴 Database Disconnected")

with st.sidebar.expander("⚙️ Connection Details", expanded=False):
    st.caption(f"**Engine:** `{db_info['type']}`")
    st.caption(f"**Target:** `{db_info['url_masked']}`")
    if db_info.get("last_error"):
        st.error(f"Error: {db_info['last_error']}")


# ---------------- LANDING PAGE ----------------

if not st.session_state.uploaded:

    # Hero Banner
    st.markdown(
        """
        <div class="hero-container" style="text-align: center; margin: 0 auto 2.5rem auto; display: flex; flex-direction: column; align-items: center; justify-content: center; max-width: 850px;">
            <div class="hero-badge" style="margin: 0 auto 1.25rem auto;">
                <span>⚡ Next-Gen Business Intelligence</span>
            </div>
            <h1 class="gradient-title" style="text-align: center; margin: 0 auto 0.85rem auto;">
                Transform Sales Data Into Growth
            </h1>
            <p class="hero-subtitle" style="text-align: center; margin: 0 auto; max-width: 680px;">
                Ingest multi-period CSV datasets, unlock real-time revenue analytics, 
                generate AI-driven business insights, and export executive PDF reports in one seamless dashboard.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Ingestion & Library Grid
    left_col, right_col = st.columns([1, 1], gap="large")

    datasets = list_datasets()
    stats = storage_stats()

    # LEFT: Saved Datasets Hub
    with left_col:
        with st.container(border=True):
            st.markdown(
                """
                <div class="chart-card-header">
                    <h3 class="chart-title">📂 Saved Dataset Hub</h3>
                    <span class="header-pill">Cloud Synced</span>
                </div>
                """,
                unsafe_allow_html=True,
            )

            if not datasets:
                st.info("No datasets saved yet. Upload a CSV file to begin your analysis.")
            else:
                st.caption(
                    f"**{stats['count']}** dataset(s) stored in Supabase · **{stats['total_rows']:,}** total records"
                )

                options = {dataset_option_label(item): item["id"] for item in datasets}
                selected_label = st.selectbox(
                    "Choose a dataset to explore",
                    options=list(options.keys()),
                    label_visibility="collapsed",
                )

                btn_col1, btn_col2 = st.columns(2)
                with btn_col1:
                    if st.button(
                        "🚀 Open Analytics",
                        type="primary",
                        width="stretch",
                        key="open_selected_dataset",
                    ):
                        if activate_dataset(options[selected_label]):
                            st.rerun()
                        st.error("Could not load the selected dataset.")

                with btn_col2:
                    if st.button(
                        "🗑️ Delete Dataset",
                        type="secondary",
                        width="stretch",
                        key="delete_selected_dataset",
                    ):
                        clear_app_cache()
                        dataset_id = options[selected_label]
                        delete_dataset(dataset_id)
                        st.rerun()

                # Library Table Preview
                with st.expander("📋 View All Stored Datasets", expanded=False):
                    library_df = pd.DataFrame(
                        [
                            {
                                "Filename": item["name"],
                                "Rows": f"{item['rows']:,}",
                                "Columns": item["columns"],
                                "Uploaded At": format_uploaded_at(item["uploaded_at"]),
                            }
                            for item in datasets
                        ]
                    )
                    st.dataframe(library_df, width="stretch", hide_index=True)

    # RIGHT: Upload Station
    with right_col:
        with st.container(border=True):
            st.markdown(
                """
                <div class="chart-card-header">
                    <h3 class="chart-title">📤 Ingest New Dataset</h3>
                    <span class="header-pill accent">CSV Ingestion</span>
                </div>
                """,
                unsafe_allow_html=True,
            )

            uploaded_file = st.file_uploader(
                "Drag and drop your sales CSV dataset here",
                type=["csv"],
                key="landing_csv_upload",
            )

            if uploaded_file is not None:
                clear_app_cache()
                status, dataset_id = process_csv_upload(uploaded_file, "landing")
                if status == "success" and dataset_id and activate_dataset(dataset_id):
                    st.success(f"✨ Successfully saved & loaded: {uploaded_file.name}")
                    st.rerun()
                elif status == "failed":
                    last_err = get_last_error()
                    st.error(
                        "Could not save or load the file. "
                        "Check your database connection and CSV format."
                    )
                    if last_err:
                        with st.expander("Database Diagnostics", expanded=False):
                            st.code(last_err)

            with st.expander("ℹ️ Supported CSV Format & Columns", expanded=False):
                st.markdown(
                    """
                    Your CSV can include the following standard columns:
                    `order_id`, `order_date`, `ship_date`, `category`, `product_name`, 
                    `region`, `sales`, `profit`, `quantity`, `discount`, `shipping_cost`.
                    """
                )
                sample_preview = pd.DataFrame({
                    "order_id": ["ORD-101", "ORD-102"],
                    "category": ["Technology", "Furniture"],
                    "sales": [1250.00, 480.50],
                    "profit": [310.20, 95.00],
                    "region": ["East", "West"],
                })
                st.dataframe(sample_preview, width="stretch", hide_index=True)

    st.markdown("<div style='margin-top: 2rem;'></div>", unsafe_allow_html=True)

    # 4 Feature Cards Grid
    f_col1, f_col2, f_col3, f_col4 = st.columns(4)

    with f_col1:
        st.markdown(
            """
            <div class="feature-card">
                <div class="feature-icon">📊</div>
                <div class="feature-title">Dynamic KPI Suite</div>
                <p class="feature-desc">Monitor total revenue, net margins, order volumes, and average transaction values in real time.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with f_col2:
        st.markdown(
            """
            <div class="feature-card">
                <div class="feature-icon">📈</div>
                <div class="feature-title">Interactive Visuals</div>
                <p class="feature-desc">Interactive time-series trends, regional profitability heatmaps, and product category rankings.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with f_col3:
        st.markdown(
            """
            <div class="feature-card">
                <div class="feature-icon">☁️</div>
                <div class="feature-title">Supabase Persistence</div>
                <p class="feature-desc">Enterprise PostgreSQL storage with automatic indexing, deduplication, and zero data loss.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with f_col4:
        st.markdown(
            """
            <div class="feature-card">
                <div class="feature-icon">📄</div>
                <div class="feature-title">Executive PDF Export</div>
                <p class="feature-desc">Generate pixel-perfect executive reports with embedded chart snapshots and KPI metrics in one click.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

# ---------------- DASHBOARD VIEW ----------------

else:
    active_id = st.session_state.get("active_dataset_id")
    df = load_dataset_cached(active_id) if active_id else load_from_database()

    if df.empty:
        st.session_state.uploaded = False
        st.rerun()

    # Normalize Dates
    if "order_date" in df.columns:
        df["order_date"] = pd.to_datetime(df["order_date"], errors="coerce")

    active_dataset = get_dataset(st.session_state.active_dataset_id)
    active_name = active_dataset["name"] if active_dataset else "Dataset"

    # ---------------- SIDEBAR WORKSPACE ----------------

    sidebar_section_label("Active Workspace")

    with st.sidebar.expander(f"📁 {active_name}", expanded=False):
        if active_dataset:
            st.caption(f"**Rows:** {active_dataset['rows']:,}")
            st.caption(f"**Saved:** {format_uploaded_at(active_dataset['uploaded_at'])}")

        others = [d for d in list_datasets_cached() if d["id"] != st.session_state.active_dataset_id]
        if others:
            switch_map = {dataset_option_label(d): d["id"] for d in others}
            picked = st.selectbox("Switch dataset", list(switch_map.keys()))
            if st.button("Load Dataset", width="stretch"):
                if activate_dataset(switch_map[picked]):
                    st.rerun()

        st.divider()

        extra = st.file_uploader(
            "Upload More CSVs",
            type=["csv"],
            accept_multiple_files=True,
            key="sidebar_csv_upload",
        )
        if extra:
            clear_app_cache()
            result = process_csv_uploads(extra, "sidebar")
            if result == "success":
                st.rerun()
            elif result == "failed":
                st.error("Upload failed. Check format.")

        st.divider()

        if st.button("⬅️ Switch to Hub", width="stretch"):
            st.session_state.uploaded = False
            st.session_state.processed_upload_landing = None
            st.session_state.processed_upload_sidebar = None
            st.rerun()

        if active_dataset and st.button("🗑️ Delete Active File", width="stretch"):
            clear_app_cache()
            delete_dataset(st.session_state.active_dataset_id)
            st.session_state.active_dataset_id = None
            st.session_state.uploaded = False
            st.rerun()

    # ---------------- SIDEBAR FILTERS ----------------

    sidebar_section_label("Analytics Filters")

    filter_parts = []
    filtered_df = df.copy()

    with st.sidebar.container(border=True):
        if "category" in df.columns:
            categories = sorted(df["category"].dropna().unique())
            sel_cat = st.multiselect("Category", options=categories, default=categories)
            if sel_cat:
                filtered_df = filtered_df[filtered_df["category"].isin(sel_cat)]
                if len(sel_cat) < len(categories):
                    filter_parts.append(f"Cat: {len(sel_cat)} sel")

        if "region" in df.columns:
            regions = sorted(df["region"].dropna().unique())
            sel_region = st.multiselect("Region", options=regions, default=regions)
            if sel_region:
                filtered_df = filtered_df[filtered_df["region"].isin(sel_region)]
                if len(sel_region) < len(regions):
                    filter_parts.append(f"Reg: {len(sel_region)} sel")

        if "order_date" in df.columns and not df["order_date"].dropna().empty:
            years = sorted(df["order_date"].dt.year.dropna().unique())
            if len(years) > 1:
                min_yr, max_yr = int(min(years)), int(max(years))
                sel_years = st.slider("Year Range", min_yr, max_yr, (min_yr, max_yr))
                filtered_df = filtered_df[
                    (filtered_df["order_date"].dt.year >= sel_years[0])
                    & (filtered_df["order_date"].dt.year <= sel_years[1])
                ]
                if sel_years != (min_yr, max_yr):
                    filter_parts.append(f"{sel_years[0]}–{sel_years[1]}")

    filter_summary = "; ".join(filter_parts) if filter_parts else "All Data"

    # ---------------- SIDEBAR EXPORT ----------------

    sidebar_section_label("Executive PDF")

    with st.sidebar.container(border=True):
        st.markdown(
            """
            <div style="font-size: 0.8rem; color: #64748b; margin-bottom: 6px;">
                Export filtered analytics, KPI metrics, and charts to an executive PDF report.
            </div>
            """,
            unsafe_allow_html=True,
        )
        try:
            pdf_bytes = get_cached_pdf(filtered_df, filter_summary)
            st.download_button(
                label="📥 Download PDF Report",
                data=pdf_bytes,
                file_name=f"Executive_Report_{active_name.replace('.csv', '')}.pdf",
                mime="application/pdf",
                width="stretch",
                type="primary",
                key="sidebar_download_pdf",
            )
        except Exception as e:
            st.caption("PDF export ready upon data load.")

    # ---------------- TOP HEADER BAR ----------------

    st.markdown(
        f"""
        <div class="dashboard-header">
            <div>
                <h1 class="dashboard-title-text">
                    📈 {active_name}
                </h1>
                <div style="font-size: 0.875rem; color: #64748b; font-weight: 500; margin-top: 4px;">
                    Displaying {len(filtered_df):,} of {len(df):,} records
                </div>
            </div>
            <div class="header-badges">
                <span class="header-pill">⚡ Status: <strong>Live</strong></span>
                <span class="header-pill accent">🔍 {filter_summary}</span>
                <span class="header-pill">☁️ Supabase PostgreSQL</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ---------------- 5 MODERN KPI CARDS ----------------

    total_sales, total_profit, total_orders, total_quantity = calculate_kpis(filtered_df)
    profit_margin = (total_profit / total_sales * 100) if total_sales > 0 else 0
    avg_ticket = (total_sales / total_orders) if total_orders > 0 else 0

    kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)

    with kpi1:
        st.markdown(
            f"""
            <div class="kpi-card">
                <div class="kpi-header">
                    <span class="kpi-title">Total Revenue</span>
                    <span class="kpi-icon">💰</span>
                </div>
                <div class="kpi-value">${total_sales:,.2f}</div>
                <div class="kpi-subtext">Avg Ticket: ${avg_ticket:,.2f}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with kpi2:
        margin_color = "#10b981" if profit_margin >= 15 else ("#f59e0b" if profit_margin >= 0 else "#ef4444")
        st.markdown(
            f"""
            <div class="kpi-card">
                <div class="kpi-header">
                    <span class="kpi-title">Net Profit</span>
                    <span class="kpi-icon">📈</span>
                </div>
                <div class="kpi-value" style="color: {margin_color};">${total_profit:,.2f}</div>
                <div class="kpi-subtext" style="color: {margin_color};">Margin: {profit_margin:.1f}%</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with kpi3:
        st.markdown(
            f"""
            <div class="kpi-card">
                <div class="kpi-header">
                    <span class="kpi-title">Total Orders</span>
                    <span class="kpi-icon">📦</span>
                </div>
                <div class="kpi-value">{total_orders:,}</div>
                <div class="kpi-subtext">Unique transaction IDs</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with kpi4:
        st.markdown(
            f"""
            <div class="kpi-card">
                <div class="kpi-header">
                    <span class="kpi-title">Units Sold</span>
                    <span class="kpi-icon">🛍️</span>
                </div>
                <div class="kpi-value">{total_quantity:,}</div>
                <div class="kpi-subtext">Total product units</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with kpi5:
        st.markdown(
            f"""
            <div class="kpi-card">
                <div class="kpi-header">
                    <span class="kpi-title">Profit Margin</span>
                    <span class="kpi-icon">🎯</span>
                </div>
                <div class="kpi-value" style="color: {margin_color};">{profit_margin:.1f}%</div>
                <div class="kpi-subtext">Net efficiency ratio</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("<div style='margin-top: 1.5rem;'></div>", unsafe_allow_html=True)

    # ---------------- 4 TABS NAVIGATION ----------------

    tab_charts, tab_insights, tab_data, tab_cloud = st.tabs([
        "📈 Visual Analytics",
        "💡 Smart Insights",
        "📋 Data Explorer",
        "☁️ Cloud Sync & Storage",
    ])

    # ---------------- TAB 1: VISUAL ANALYTICS ----------------

    with tab_charts:
        row1_col1, row1_col2 = st.columns([1.2, 1], gap="medium")

        # Sales Trend Over Time
        with row1_col1:
            with st.container(border=True):
                st.markdown(
                    """
                    <div class="chart-card-header">
                        <h3 class="chart-title">📈 Revenue & Sales Momentum</h3>
                        <span class="header-pill">Time Series</span>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                trend_df = sales_trend(filtered_df)
                if not trend_df.empty:
                    fig1 = px.area(
                        trend_df,
                        x="order_date",
                        y="sales",
                        markers=True,
                    )
                    fig1.update_traces(
                        line_color="#38bdf8",
                        fillcolor="rgba(56, 189, 248, 0.15)",
                    )
                    fig1.update_layout(
                        xaxis=dict(rangeslider=dict(visible=True), type="date"),
                        height=420,
                        margin=dict(l=10, r=10, t=20, b=10),
                    )
                    apply_chart_theme(fig1, dark_mode)
                    st.plotly_chart(fig1, width="stretch")
                else:
                    st.info("Insufficient date/sales data for trend analysis.")

        # Category Performance Breakdown
        with row1_col2:
            with st.container(border=True):
                st.markdown(
                    """
                    <div class="chart-card-header">
                        <h3 class="chart-title">🏷️ Category Distribution</h3>
                        <span class="header-pill">Share</span>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                category_df = category_analysis(filtered_df)
                if not category_df.empty:
                    fig2 = px.pie(
                        category_df,
                        names="category",
                        values="sales",
                        hole=0.55,
                    )
                    fig2.update_traces(
                        textposition="inside",
                        textinfo="percent+label",
                        marker=dict(line=dict(color="#0f172a" if dark_mode else "#ffffff", width=2)),
                    )
                    fig2.update_layout(
                        height=420,
                        margin=dict(l=10, r=10, t=20, b=10),
                        showlegend=False,
                    )
                    apply_chart_theme(fig2, dark_mode)
                    st.plotly_chart(fig2, width="stretch")
                else:
                    st.info("No category data found.")

        st.markdown("<div style='margin-top: 1rem;'></div>", unsafe_allow_html=True)

        row2_col1, row2_col2 = st.columns([1, 1.2], gap="medium")

        # Regional Profitability
        with row2_col1:
            with st.container(border=True):
                st.markdown(
                    """
                    <div class="chart-card-header">
                        <h3 class="chart-title">🗺️ Regional Profitability</h3>
                        <span class="header-pill">Margin</span>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                region_df = region_analysis(filtered_df)
                if not region_df.empty:
                    fig3 = px.bar(
                        region_df,
                        x="region",
                        y="profit",
                        color="profit",
                        color_continuous_scale="Viridis",
                    )
                    fig3.update_layout(
                        height=380,
                        margin=dict(l=10, r=10, t=20, b=10),
                        coloraxis_showscale=False,
                    )
                    apply_chart_theme(fig3, dark_mode)
                    st.plotly_chart(fig3, width="stretch")
                else:
                    st.info("No region data found.")

        # Top 10 Best Selling Products
        with row2_col2:
            with st.container(border=True):
                st.markdown(
                    """
                    <div class="chart-card-header">
                        <h3 class="chart-title">🏆 Top 10 Best-Selling Products</h3>
                        <span class="header-pill">Rankings</span>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                top_p_df = top_products(filtered_df)
                if not top_p_df.empty:
                    fig4 = px.bar(
                        top_p_df,
                        x="sales",
                        y="product_name",
                        orientation="h",
                        color="sales",
                        color_continuous_scale="Blues",
                    )
                    fig4.update_layout(
                        yaxis=dict(autorange="reversed"),
                        height=380,
                        margin=dict(l=10, r=10, t=20, b=10),
                        coloraxis_showscale=False,
                    )
                    apply_chart_theme(fig4, dark_mode)
                    st.plotly_chart(fig4, width="stretch")
                else:
                    st.info("No product ranking data available.")

    # ---------------- TAB 2: SMART INSIGHTS ----------------

    with tab_insights:
        st.markdown(
            """
            <div class="chart-card-header">
                <h3 class="chart-title">💡 Automated Business Intelligence</h3>
                <span class="header-pill accent">Executive Summary</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

        insights = generate_insights(filtered_df)

        if insights:
            for idx, insight in enumerate(insights):
                # Categorize based on content keywords
                if "strongest" in insight.lower() or "highest" in insight.lower():
                    card_class = "success"
                    icon = "🟢"
                elif "weakest" in insight.lower() or "lowest" in insight.lower():
                    card_class = "warning"
                    icon = "🟡"
                elif "negative" in insight.lower() or "loss" in insight.lower():
                    card_class = "danger"
                    icon = "🔴"
                else:
                    card_class = "info"
                    icon = "🔵"

                st.markdown(
                    f"""
                    <div class="insight-card {card_class}">
                        <div class="insight-icon">{icon}</div>
                        <div>
                            <p class="insight-text">{insight}</p>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
        else:
            st.info("No automated insights could be derived from current filters.")

    # ---------------- TAB 3: DATA EXPLORER ----------------

    with tab_data:
        st.markdown(
            """
            <div class="chart-card-header">
                <h3 class="chart-title">📋 Raw Records Explorer</h3>
                <span class="header-pill">Searchable</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

        d_col1, d_col2, d_col3, d_col4 = st.columns(4)
        summary = dataset_summary(filtered_df)

        d_col1.metric("Total Filtered Rows", f"{summary['Rows']:,}")
        d_col2.metric("Total Columns", summary["Columns"])
        d_col3.metric("Missing Fields", summary["Missing Values"])
        d_col4.metric("Duplicates Filtered", summary["Duplicate Rows"])

        st.markdown("<div style='margin-top: 1rem;'></div>", unsafe_allow_html=True)

        with st.container(border=True):
            st.dataframe(
                filtered_df,
                width="stretch",
                hide_index=True,
            )

            csv_data = filtered_df.to_csv(index=False).encode("utf-8")
            st.download_button(
                label="📥 Export Filtered CSV",
                data=csv_data,
                file_name="filtered_business_data.csv",
                mime="text/csv",
            )

    # ---------------- TAB 4: CLOUD SYNC & STORAGE ----------------

    with tab_cloud:
        st.markdown(
            """
            <div class="chart-card-header">
                <h3 class="chart-title">☁️ Supabase Cloud & Persistence</h3>
                <span class="header-pill accent">PostgreSQL</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

        c_col1, c_col2 = st.columns(2, gap="large")

        with c_col1:
            with st.container(border=True):
                st.subheader("Database Diagnostics")
                cloud_stats = storage_stats()
                st.write(f"**Database Engine:** `{db_info['type']}`")
                st.write(f"**Cluster URI:** `{db_info['url_masked']}`")
                st.write(f"**Connection Status:** {'🟢 Healthy' if db_info['connected'] else '🔴 Error'}")
                st.write(f"**Total Stored Datasets:** `{cloud_stats['count']}`")
                st.write(f"**Total Stored Records:** `{cloud_stats['total_rows']:,}`")

                if st.button("🔄 Test Connection Ping", key="ping_db"):
                    if test_database_connection():
                        st.success("⚡ Database responded with latency < 50ms!")
                    else:
                        st.error("Database connection check failed.")

        with c_col2:
            with st.container(border=True):
                st.subheader("Dataset Clean Up & De-duplication")
                st.caption(
                    "Keep your database clean by removing older versions of identical uploads."
                )
                dup_info = count_duplicate_datasets()
                if dup_info["total"] > 0:
                    st.warning(f"⚠️ Found {dup_info['total']} duplicate datasets.")
                else:
                    st.success("✨ All saved datasets are unique.")

                if st.button("🧹 Run Cloud Cleanup", type="secondary", key="run_cleanup_tab"):
                    result = run_dataset_cleanup()
                    st.success(f"Removed {result['removed']} redundant copy/copies.")
                    st.rerun()

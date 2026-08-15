from datetime import datetime
from io import BytesIO

import matplotlib
matplotlib.use("Agg")  # Non-interactive backend for headless cloud servers
import matplotlib.pyplot as plt
import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    Image,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from analysis import (
    calculate_kpis,
    category_analysis,
    generate_insights,
    region_analysis,
    sales_trend,
    top_products,
)

# Harmonious Curated Color Palette
CHART_COLORS = ["#2563eb", "#38bdf8", "#10b981", "#f59e0b", "#8b5cf6", "#ec4899", "#06b6d4", "#ef4444"]


def _generate_sales_trend_image(trend_df: pd.DataFrame) -> bytes:
    """Generate Sales Trend Area chart as high-res PNG bytes."""
    fig, ax = plt.subplots(figsize=(8.2, 3.2), dpi=200)
    fig.patch.set_facecolor("#ffffff")
    ax.set_facecolor("#fafbfc")

    dates = pd.to_datetime(trend_df["order_date"])
    sales = trend_df["sales"]

    ax.plot(dates, sales, color="#2563eb", linewidth=2.2, marker="o", markersize=3.5)
    ax.fill_between(dates, sales, color="#2563eb", alpha=0.15)

    ax.set_title("Revenue & Sales Momentum Over Time", fontsize=11, fontweight="bold", color="#0f172a", pad=10)
    ax.tick_params(axis="both", which="major", labelsize=8.5, colors="#334155")
    ax.grid(True, linestyle="--", alpha=0.5, color="#cbd5e1")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color("#cbd5e1")
    ax.spines["bottom"].set_color("#cbd5e1")
    fig.tight_layout()

    buf = BytesIO()
    plt.savefig(buf, format="png", bbox_inches="tight", pad_inches=0.08, dpi=200)
    plt.close(fig)
    buf.seek(0)
    return buf.getvalue()


def _generate_category_pie_image(category_df: pd.DataFrame) -> bytes:
    """Generate Category Sales Distribution Donut / Pie Chart with clear legend and aligned layout."""
    fig, ax = plt.subplots(figsize=(8.2, 3.2), dpi=200)
    fig.patch.set_facecolor("#ffffff")

    labels = category_df["category"].tolist()
    values = category_df["sales"].tolist()
    palette = CHART_COLORS[: len(labels)]

    wedges, texts, autotexts = ax.pie(
        values,
        autopct="%1.1f%%",
        startangle=140,
        colors=palette,
        pctdistance=0.72,
        wedgeprops=dict(width=0.44, edgecolor="#ffffff", linewidth=2),
    )

    for autotext in autotexts:
        autotext.set_color("#ffffff")
        autotext.set_fontsize(9)
        autotext.set_fontweight("bold")

    ax.axis("equal")

    # Clean, nicely aligned legend on the right
    ax.legend(
        wedges,
        [f"{lbl} (${val:,.0f})" for lbl, val in zip(labels, values)],
        title="Product Categories",
        loc="center left",
        bbox_to_anchor=(0.88, 0.5),
        frameon=False,
        fontsize=9,
        title_fontsize=9.5,
    )

    ax.set_title("Category Sales Distribution", fontsize=11, fontweight="bold", color="#0f172a", pad=10)
    fig.tight_layout()

    buf = BytesIO()
    plt.savefig(buf, format="png", bbox_inches="tight", pad_inches=0.08, dpi=200)
    plt.close(fig)
    buf.seek(0)
    return buf.getvalue()


def _generate_region_bar_image(region_df: pd.DataFrame) -> bytes:
    """Generate Regional Profitability Bar Chart as high-res PNG bytes."""
    fig, ax = plt.subplots(figsize=(8.2, 3.2), dpi=200)
    fig.patch.set_facecolor("#ffffff")
    ax.set_facecolor("#fafbfc")

    regions = region_df["region"].tolist()
    profits = region_df["profit"].tolist()
    palette = [CHART_COLORS[i % len(CHART_COLORS)] for i in range(len(regions))]

    bars = ax.bar(regions, profits, color=palette, width=0.5, edgecolor="#ffffff", linewidth=1.2)
    ax.set_title("Regional Profitability Breakdown", fontsize=11, fontweight="bold", color="#0f172a", pad=10)
    ax.tick_params(axis="both", which="major", labelsize=8.5, colors="#334155")
    ax.grid(axis="y", linestyle="--", alpha=0.5, color="#cbd5e1")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color("#cbd5e1")
    ax.spines["bottom"].set_color("#cbd5e1")

    for bar in bars:
        height = bar.get_height()
        ax.annotate(
            f"${height:,.0f}",
            xy=(bar.get_x() + bar.get_width() / 2, height),
            xytext=(0, 3),
            textcoords="offset points",
            ha="center",
            va="bottom",
            fontsize=8,
            color="#0f172a",
            fontweight="bold",
        )

    fig.tight_layout()
    buf = BytesIO()
    plt.savefig(buf, format="png", bbox_inches="tight", pad_inches=0.08, dpi=200)
    plt.close(fig)
    buf.seek(0)
    return buf.getvalue()


def _generate_top_products_image(top_p_df: pd.DataFrame) -> bytes:
    """Generate Top 10 Products Horizontal Bar Chart as high-res PNG bytes."""
    fig, ax = plt.subplots(figsize=(8.2, 3.3), dpi=200)
    fig.patch.set_facecolor("#ffffff")
    ax.set_facecolor("#fafbfc")

    sorted_df = top_p_df.sort_values(by="sales", ascending=True)
    products = [p[:26] + "..." if len(p) > 26 else p for p in sorted_df["product_name"]]
    sales = sorted_df["sales"]

    bars = ax.barh(products, sales, color="#38bdf8", height=0.6, edgecolor="#ffffff", linewidth=1)
    ax.set_title("Top 10 Best-Selling Products by Revenue", fontsize=11, fontweight="bold", color="#0f172a", pad=10)
    ax.tick_params(axis="both", which="major", labelsize=8, colors="#334155")
    ax.grid(axis="x", linestyle="--", alpha=0.5, color="#cbd5e1")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color("#cbd5e1")
    ax.spines["bottom"].set_color("#cbd5e1")

    fig.tight_layout()
    buf = BytesIO()
    plt.savefig(buf, format="png", bbox_inches="tight", pad_inches=0.08, dpi=200)
    plt.close(fig)
    buf.seek(0)
    return buf.getvalue()


def generate_dashboard_pdf(
    df: pd.DataFrame,
    filter_summary: str | None = None,
) -> bytes:
    """Build a beautifully spaced executive PDF report with KPIs, Pie charts, trends, and insights."""
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=0.5 * inch,
        leftMargin=0.5 * inch,
        topMargin=0.5 * inch,
        bottomMargin=0.5 * inch,
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "ReportTitle",
        parent=styles["Heading1"],
        fontSize=18,
        spaceAfter=3,
        textColor=colors.HexColor("#0f172a"),
        fontName="Helvetica-Bold",
    )
    subtitle_style = ParagraphStyle(
        "ReportSubtitle",
        parent=styles["Normal"],
        fontSize=9.5,
        textColor=colors.HexColor("#475569"),
        spaceAfter=10,
        fontName="Helvetica",
    )
    section_style = ParagraphStyle(
        "SectionHeading",
        parent=styles["Heading2"],
        fontSize=12,
        spaceBefore=8,
        spaceAfter=4,
        textColor=colors.HexColor("#1e40af"),
        fontName="Helvetica-Bold",
    )
    insight_style = ParagraphStyle(
        "Insight",
        parent=styles["Normal"],
        fontSize=9.5,
        leftIndent=6,
        spaceAfter=4,
        textColor=colors.HexColor("#1e293b"),
        fontName="Helvetica",
    )

    story = []
    generated_at = datetime.now().strftime("%B %d, %Y at %I:%M %p")

    # 1. Header
    story.append(Paragraph("Executive Business Analytics Report", title_style))
    story.append(Paragraph(f"Generated on {generated_at} · PulseAnalytics Platform", subtitle_style))

    if filter_summary:
        story.append(Paragraph(f"<b>Applied Filters:</b> {filter_summary}", subtitle_style))

    # 2. KPI Summary Section
    total_sales, total_profit, total_orders, total_quantity = calculate_kpis(df)
    profit_margin = (total_profit / total_sales * 100) if total_sales > 0 else 0
    avg_ticket = (total_sales / total_orders) if total_orders > 0 else 0

    story.append(Paragraph("Executive Summary & Key Metrics", section_style))

    kpi_data = [
        ["Key Metric", "Value", "Metric Description"],
        ["Total Revenue", f"${total_sales:,.2f}", f"Avg transaction ticket: ${avg_ticket:,.2f}"],
        ["Net Profit", f"${total_profit:,.2f}", f"Profit Margin: {profit_margin:.1f}%"],
        ["Total Orders", f"{total_orders:,}", "Unique completed transactions"],
        ["Units Sold", f"{total_quantity:,}", "Total physical product volume"],
    ]

    kpi_table = Table(kpi_data, colWidths=[2.2 * inch, 2.0 * inch, 3.3 * inch])
    kpi_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e40af")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, 0), 9.5),
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
                ("FONTSIZE", (0, 1), (-1, -1), 9),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ]
        )
    )
    story.append(kpi_table)
    story.append(Spacer(1, 0.12 * inch))

    # 3. Business Insights
    insights = generate_insights(df)
    if insights:
        story.append(Paragraph("Key Business Insights & Observations", section_style))
        for insight in insights:
            story.append(Paragraph(f"• {insight}", insight_style))
        story.append(Spacer(1, 0.1 * inch))

    # 4. Visual Analytics & Charts
    page_width = letter[0] - 1.0 * inch

    chart_images = []

    # 1. Sales Trend
    trend_df = sales_trend(df)
    if not trend_df.empty:
        try:
            png_data = _generate_sales_trend_image(trend_df)
            if png_data:
                chart_images.append(("Revenue Trend Over Time", png_data))
        except Exception:
            pass

    # 2. Category Pie / Donut Chart (Aligned & Proportional)
    category_df = category_analysis(df)
    if not category_df.empty:
        try:
            png_data = _generate_category_pie_image(category_df)
            if png_data:
                chart_images.append(("Category Sales Distribution (Pie Chart)", png_data))
        except Exception:
            pass

    # 3. Regional Bar
    region_df = region_analysis(df)
    if not region_df.empty:
        try:
            png_data = _generate_region_bar_image(region_df)
            if png_data:
                chart_images.append(("Regional Profitability Analysis", png_data))
        except Exception:
            pass

    # 4. Top Products
    top_p_df = top_products(df)
    if not top_p_df.empty:
        try:
            png_data = _generate_top_products_image(top_p_df)
            if png_data:
                chart_images.append(("Top 10 Best-Selling Products", png_data))
        except Exception:
            pass

    if chart_images:
        story.append(PageBreak())
        story.append(Paragraph("Visual Analytics & Distribution", title_style))
        story.append(Spacer(1, 0.08 * inch))

        for index, (chart_title, img_bytes) in enumerate(chart_images):
            img_buf = BytesIO(img_bytes)
            story.append(Paragraph(chart_title, section_style))
            img = Image(img_buf, width=page_width, height=page_width * 0.39)
            story.append(img)
            story.append(Spacer(1, 0.08 * inch))

            # Neatly group 2 charts per page
            if index % 2 == 1 and index < len(chart_images) - 1:
                story.append(PageBreak())

    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()

from datetime import datetime
from io import BytesIO

import pandas as pd
import plotly.express as px
from plotly.io import to_image
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

CHART_COLORS = [
    "#38bdf8",  # Sky Blue
    "#818cf8",  # Indigo
    "#34d399",  # Emerald
    "#f472b6",  # Pink
    "#fbbf24",  # Amber
    "#a78bfa",  # Violet
    "#2dd4bf",  # Teal
    "#f87171",  # Red
]

CHART_LAYOUT = dict(
    plot_bgcolor="#ffffff",
    paper_bgcolor="#ffffff",
    font=dict(color="#0f172a", family="Helvetica", size=11),
    margin=dict(l=40, r=40, t=40, b=40),
    colorway=CHART_COLORS,
)


def _apply_chart_export_style(fig, chart_type: str):
    """Format figures for clean, high-resolution rendering in PDF."""
    fig.update_layout(**CHART_LAYOUT)

    if chart_type == "line":
        fig.update_traces(
            line=dict(color="#2563eb", width=3),
            marker=dict(
                color="#2563eb",
                size=8,
                line=dict(width=1, color="#ffffff"),
            ),
            fill="tozeroy",
            fillcolor="rgba(37, 99, 235, 0.18)",
        )
        fig.update_layout(
            xaxis=dict(
                rangeslider=dict(visible=False),
                type="date",
                gridcolor="#e2e8f0",
                linecolor="#cbd5e1",
            ),
            yaxis=dict(gridcolor="#e2e8f0", linecolor="#cbd5e1"),
            height=380,
        )

    elif chart_type == "pie":
        fig.update_traces(
            textposition="inside",
            textinfo="percent+label",
            marker=dict(line=dict(color="#ffffff", width=2)),
            textfont=dict(size=11, color="#ffffff"),
        )
        fig.update_layout(
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=-0.15,
                xanchor="center",
                x=0.5,
            ),
            height=380,
        )

    elif chart_type == "bar":
        fig.update_traces(
            marker=dict(
                line=dict(color="#ffffff", width=1),
                opacity=0.95,
            ),
        )
        fig.update_layout(
            xaxis=dict(gridcolor="#e2e8f0", linecolor="#cbd5e1"),
            yaxis=dict(gridcolor="#e2e8f0", linecolor="#cbd5e1"),
            showlegend=False,
            height=380,
        )


def _fig_to_image(fig, width=900, height=420):
    fig.update_layout(height=height, width=width)
    try:
        return to_image(
            fig,
            format="png",
            width=width,
            height=height,
            scale=2,
            engine="kaleido",
        )
    except Exception:
        try:
            return fig.to_image(format="png", width=width, height=height)
        except Exception:
            return b""


def _build_chart_figures(df):
    charts = []

    # 1. Sales Trend Area / Line Chart
    trend_df = sales_trend(df)
    if not trend_df.empty:
        fig1 = px.line(
            trend_df,
            x="order_date",
            y="sales",
            markers=True,
            title="Revenue & Sales Trend Over Time",
        )
        _apply_chart_export_style(fig1, "line")
        charts.append(("Revenue Trend Over Time", fig1))

    # 2. Category Distribution PIE / DONUT Chart
    category_df = category_analysis(df)
    if not category_df.empty:
        fig2 = px.pie(
            category_df,
            names="category",
            values="sales",
            hole=0.45,
            title="Sales Distribution by Category",
            color_discrete_sequence=CHART_COLORS,
        )
        _apply_chart_export_style(fig2, "pie")
        charts.append(("Category Sales Distribution (Pie Chart)", fig2))

    # 3. Regional Profitability Bar Chart
    region_df = region_analysis(df)
    if not region_df.empty:
        fig3 = px.bar(
            region_df,
            x="region",
            y="profit",
            color="region",
            color_discrete_sequence=CHART_COLORS,
            title="Regional Profitability",
            text="profit",
        )
        fig3.update_traces(
            texttemplate="$%{text:,.0f}",
            textposition="outside",
        )
        _apply_chart_export_style(fig3, "bar")
        charts.append(("Regional Profitability Analysis", fig3))

    # 4. Top 10 Best-Selling Products
    top_p_df = top_products(df)
    if not top_p_df.empty:
        fig4 = px.bar(
            top_p_df,
            x="sales",
            y="product_name",
            orientation="h",
            color="sales",
            color_continuous_scale="Blues",
            title="Top 10 Best-Selling Products",
        )
        fig4.update_layout(yaxis=dict(autorange="reversed"))
        _apply_chart_export_style(fig4, "bar")
        charts.append(("Top 10 Best-Selling Products", fig4))

    return charts


def generate_dashboard_pdf(
    df: pd.DataFrame,
    filter_summary: str | None = None,
) -> bytes:
    """Build a comprehensive executive PDF report with KPIs, Pie charts, trends, and insights."""
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
        fontSize=20,
        spaceAfter=4,
        textColor=colors.HexColor("#0f172a"),
        fontName="Helvetica-Bold",
    )
    subtitle_style = ParagraphStyle(
        "ReportSubtitle",
        parent=styles["Normal"],
        fontSize=10,
        textColor=colors.HexColor("#475569"),
        spaceAfter=12,
        fontName="Helvetica",
    )
    section_style = ParagraphStyle(
        "SectionHeading",
        parent=styles["Heading2"],
        fontSize=13,
        spaceBefore=10,
        spaceAfter=6,
        textColor=colors.HexColor("#1e40af"),
        fontName="Helvetica-Bold",
    )
    insight_style = ParagraphStyle(
        "Insight",
        parent=styles["Normal"],
        fontSize=10,
        leftIndent=8,
        spaceAfter=6,
        textColor=colors.HexColor("#1e293b"),
        fontName="Helvetica",
    )

    story = []
    generated_at = datetime.now().strftime("%B %d, %Y at %I:%M %p")

    # Header
    story.append(Paragraph("Executive Business Analytics Report", title_style))
    story.append(Paragraph(f"Generated on {generated_at} · PulseAnalytics Platform", subtitle_style))

    if filter_summary:
        story.append(Paragraph(f"<b>Applied Filters:</b> {filter_summary}", subtitle_style))

    # KPI Summary Section
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

    kpi_table = Table(kpi_data, colWidths=[2.2 * inch, 2.0 * inch, 3.2 * inch])
    kpi_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e40af")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, 0), 10),
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
                ("FONTSIZE", (0, 1), (-1, -1), 9.5),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ]
        )
    )
    story.append(kpi_table)
    story.append(Spacer(1, 0.2 * inch))

    # Business Insights Section on First Page
    insights = generate_insights(df)
    if insights:
        story.append(Paragraph("Key Business Insights & Observations", section_style))
        for insight in insights:
            story.append(Paragraph(f"• {insight}", insight_style))
        story.append(Spacer(1, 0.15 * inch))

    # Analytics Charts with Pie Chart
    charts = _build_chart_figures(df)
    if charts:
        story.append(PageBreak())
        story.append(Paragraph("Visual Analytics & Distribution", title_style))
        story.append(Spacer(1, 0.1 * inch))

        page_width = letter[0] - 1.0 * inch

        for index, (chart_title, fig) in enumerate(charts):
            png_bytes = _fig_to_image(fig, width=900, height=420)
            img_buffer = BytesIO(png_bytes)

            story.append(Paragraph(chart_title, section_style))
            img = Image(img_buffer, width=page_width, height=page_width * 0.46)
            story.append(img)
            story.append(Spacer(1, 0.15 * inch))

            # Break every 2 charts for neat 2-chart per page layout
            if index % 2 == 1 and index < len(charts) - 1:
                story.append(PageBreak())

    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()

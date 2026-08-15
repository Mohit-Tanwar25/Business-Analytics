# 📊 PulseAnalytics — Enterprise Business Intelligence Platform

An interactive, high-performance Business Intelligence and Sales Analytics dashboard built with **Streamlit**, **Plotly**, and **Supabase PostgreSQL**.

---

## 🚀 Key Features

- **⚡ Cloud PostgreSQL Integration**: Powered by Supabase for high-speed multi-dataset persistence, deduplication, and zero-crash fallback.
- **📈 Dynamic KPI Dashboard**: Real-time tracking of Total Revenue, Net Profit, Orders, Physical Units Sold, and Profit Margin %.
- **📊 Interactive Visuals**:
  - Revenue Trend Area Line chart with date range sliders.
  - Category Distribution Donut / Pie chart with percentage breakdowns.
  - Regional Profitability & Shipping cost analysis.
  - Top 10 Best-Selling Products ranking.
- **💡 Automated Business Insights**: AI/rule-based operational summaries highlighting key strengths, margin warnings, and revenue drivers.
- **📄 Executive PDF Reports**: 1-click vector-grade PDF export complete with KPI summaries, charts, and bulletpoint observations.
- **🌙 Glassmorphism Theme System**: High-contrast Light & Dark modes powered by the *Plus Jakarta Sans* design system.

---

## 🛠️ Technology Stack

- **Frontend / Framework**: [Streamlit](https://streamlit.io/)
- **Visualizations**: [Plotly Express](https://plotly.com/python/)
- **Database**: [Supabase](https://supabase.com/) (PostgreSQL) / [SQLAlchemy](https://www.sqlalchemy.org/)
- **Data Processing**: [Pandas](https://pandas.pydata.org/) & [NumPy](https://numpy.org/)
- **PDF Engine**: [ReportLab](https://www.reportlab.com/) & [Kaleido](https://github.com/plotly/Kaleido)

---

## 📦 Installation & Setup

### 1. Clone the Repository
```bash
git clone https://github.com/YOUR-USERNAME/YOUR-REPO-NAME.git
cd "Business analysis system"
```

### 2. Set Up Virtual Environment & Dependencies
```bash
python -m venv .venv
# On Windows:
.venv\Scripts\activate
# On macOS/Linux:
source .venv/bin/activate

pip install -r requirements.txt
```

### 3. Database Setup (Supabase)
1. Create a free PostgreSQL database at [supabase.com](https://supabase.com).
2. Open the **SQL Editor** in Supabase and execute the script in [`supabase_schema.sql`](supabase_schema.sql).
3. Copy your project connection string from Supabase (**Connect** ➔ **URI**).

### 4. Configure Secrets
Create a `.streamlit/secrets.toml` file (or `.env`):

```toml
# .streamlit/secrets.toml
SUPABASE_DB_URL = "postgresql://postgres.[PROJECT-REF]:[PASSWORD]@aws-0-[REGION].pooler.supabase.com:6543/postgres?sslmode=require"
```
*(Copy from [`.streamlit/secrets.toml.example`](.streamlit/secrets.toml.example) as reference).*

---

## 🚀 Running the Application

```bash
streamlit run app.py
```

---

## 📂 Project Structure

```
├── app.py                     # Main Streamlit application and UI layout
├── database.py                # Database connection, PostgreSQL bulk ingestion & caching
├── file_storage.py            # Dataset upload management API
├── analysis.py                # Business logic, KPIs, and insight calculations
├── theme.py                   # Synchronous Dark/Light theme engine & Plotly themes
├── pdf_export.py              # ReportLab vector PDF generator with embedded charts
├── style.css                  # Custom Glassmorphism CSS design system
├── supabase_schema.sql        # Supabase PostgreSQL DDL and RLS policies
├── sales_data_500.csv         # Sample dataset for immediate testing
├── requirements.txt           # Python dependencies
└── .gitignore                 # Security exclusion rules
```

---

## 📄 License
MIT License. Free for personal and commercial use.

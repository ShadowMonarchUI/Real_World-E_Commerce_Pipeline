# 📊 E-Commerce Analytics Dashboard & Ingestion Pipeline

An enterprise-grade transactional analytics suite showcasing a high-performance **Streamlit** dashboard styled in a premium **Power BI / Excel Light Theme**, backed by an optimized data cleaning pipeline and a multi-threaded database uploader connected to an **Aiven Cloud MySQL** database.

---

## 🚀 Key Features

### 1. High-Contrast Power BI Light Theme
- **Consistent Styling**: Styled with a corporate light gray canvas (`#f3f2f1`), clean white visual cards (`#ffffff`), and dark corporate navy headers (`#092a47`).
- **High Contrast Widget Controls**: Universal CSS rules ensure all dropdowns, multiselect tags, expanders, forms, and sliders display in high-contrast charcoal (`#252423`) on light backgrounds, preventing text from blending under OS-forced browser dark themes.
- **Equal-Height Metric Cards**: Top KPI cards align perfectly in a single row with dynamic font sizing (`clamp()`) to fit large numbers cleanly on one line, complete with exact values visible on mouse hover tooltips.

### 2. 11 Rich Interactive Visualizations
Each chart is encapsulated in a crisp card border (`st.container(border=True)`) and formatted with data labels, reference averages, or trendlines:
- **Executive Overview**:
  - *Monthly Sales revenue Trend*: Line chart with monthly labels and a dashed red Monthly Average reference line.
  - *Regional Revenue Contribution Share*: Donut chart featuring the total aggregate sales dynamically displayed inside the center hole.
  - *Weekday Sales Distribution*: Bar chart that highlights the peak sales day in deep navy, with a dashed red Daily Average reference line.
  - *Cumulative Revenue Growth*: Area chart plotting the running total revenue over time.
  - *Monthly Average Order Value (AOV) Trend*: Line chart tracking average ticket sizes over time.
- **Product Insights**:
  - *Top 10 Products by Revenue & Top 10 Products by Volume*: Two side-by-side bar charts comparing sales value vs. inventory volumes.
  - *Unit Price Frequency Distribution*: Histogram showing pricing spreads with indicators for mean and median item prices.
  - *Price vs. Quantity Correlation*: Scatter plot overlaying a manually-computed OLS linear regression line showing pricing elasticity.
- **Customer Analytics**:
  - *Top 10 Spending Customers*: Bar chart tracking VIP corporate accounts.
  - *Purchasing Activity Trends by Hour*: Smooth area chart showing peak purchase hours, highlighting the peak business window (10:00 AM - 3:00 PM) in a shaded region.
  - *Customer Purchase Frequency*: Loyalty cohorts bar chart segmenting repeat buyers.

### 3. High-Performance Database Ingestion
- **Fast C-Ingestion**: Ingests all **530,104 transactional rows** from Aiven Cloud MySQL in **5.65 seconds** (using native C extensions instead of pure Python).
- **Date Ingestion Speedup**: Speeds up date parsing 10x by bypassing date-inference string checks via explicit formatting (`format='%m/%d/%y %H:%M'`).
- **Threaded Uploader**: Uploads records in chunks of 10,000 using a thread pool with exponential backoff retry logic to handle cloud database rate limits without deadlocking.
- **Robust Cache Fallback**: Seamlessly loads a local CSV file if the remote database connection fails.

---

## 📂 Project Directory Structure

```text
├── .streamlit/
│   ├── config.toml           # Streamlit global theme settings
│   └── secrets.toml          # Database credentials (locally excluded from Git)
├── app.py                    # Main dashboard application code
├── data_cleaner.py           # Optimized raw CSV cleaning pipeline (Pandas)
├── upload.py                 # Multi-threaded database uploader with retry logic
├── db_schema.py              # Diagnostic script to verify table schema & indexes
├── requirements.txt          # Python dependencies list
└── README.md                 # Project documentation
```

---

## 🛠️ Installation & Setup

### 1. Clone & Set Up Environment
```bash
git clone https://github.com/ShadowMonarchUI/Real_World-E_Commerce_Pipeline.git
cd Real_World-E_Commerce_Pipeline
python -m venv venv
venv\Scripts\activate
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure Database Credentials
Create a `.streamlit/secrets.toml` file in the project root:
```toml
[mysql]
host = "e-commerce-pipeline-bordockz-3737.c.aivencloud.com"
port = 14582
database = "ecommerce_analytics"
user = "avnadmin"
password = "YOUR_AIVEN_PASSWORD_HERE"
```

### 4. Run the Data Pipeline
Clean raw data and upload it to the cloud database:
```bash
# 1. Clean raw_online_retail.csv -> samplesuperstore.csv
python data_cleaner.py

# 2. Upload clean samplesuperstore.csv to MySQL
python upload.py
```

### 5. Launch the Dashboard
```bash
streamlit run app.py
```

---

## 🗄️ Database Schema
The SQL database is built on the following schema:

| Column Name | SQL Type | Description |
|---|---|---|
| **OrderID** | `VARCHAR(50)` | Transaction order identifier |
| **ProductID** | `VARCHAR(50)` | Product SKU code |
| **ProductName**| `VARCHAR(255)`| Name of the item sold |
| **Quantity** | `INT` | Quantity purchased |
| **OrderDate** | `DATETIME` | Time of sale |
| **Price** | `DECIMAL(10,2)`| Unit price |
| **Sales** | `DECIMAL(15,2)`| Total line revenue (Quantity * Price) |
| **CustomerID** | `VARCHAR(50)` | Customer account ID |
| **Region** | `VARCHAR(100)`| Country/region of purchase |

---

## 🛡️ Security
- **No Hardcoded Credentials**: Database scripts dynamically read connection settings from `.streamlit/secrets.toml` at runtime.
- **Git Shield**: `.gitignore` is configured to prevent committing `.streamlit/secrets.toml` and large CSV datasets.

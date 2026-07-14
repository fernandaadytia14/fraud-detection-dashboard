import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import time
import random
import string
import warnings
from datetime import datetime, timedelta

warnings.filterwarnings('ignore')

# ============================================================
# KONFIGURASI HALAMAN
# ============================================================
st.set_page_config(
    page_title="Credit Card Fraud Detection - Live Dashboard",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    .block-container { padding-top: 1rem; }
    h1 { color: #ffffff; font-size: 2rem; font-weight: 700; }
    h2 { color: #ffffff; font-size: 1.4rem; font-weight: 600; }
    h3 { color: #ffffff; }
    section[data-testid="stSidebar"] { display: none; }
    .stMetric {
        background-color: #1e2130;
        border-radius: 12px;
        padding: 1rem;
        border: 1px solid #2e3250;
    }
    .stMetric label { color: #a0aec0 !important; font-size: 0.85rem; }
    .stMetric div { color: #ffffff !important; font-size: 1.8rem; font-weight: 700; }
    </style>
""", unsafe_allow_html=True)

# ============================================================
# INISIALISASI SESSION STATE
# ============================================================
if 'transaction_count' not in st.session_state:
    st.session_state.transaction_count = 0
if 'fraud_count' not in st.session_state:
    st.session_state.fraud_count = 0
if 'transaction_log' not in st.session_state:
    st.session_state.transaction_log = []
if 'last_timestamp' not in st.session_state:
    st.session_state.last_timestamp = datetime.now()
if 'last_index' not in st.session_state:
    st.session_state.last_index = 0

# ============================================================
# LOAD DATA
# ============================================================
@st.cache_data
def load_data():
    import gdown
    import os
    output = "creditcard.csv"
    if not os.path.exists(output):
        file_id = "17rJlezUB3oaA8swlWmeOG824P8VSt_JD"
        gdown.download(id=file_id, output=output, quiet=False)
    df = pd.read_csv(output)
    df['Hour'] = (df['Time'] / 3600).astype(int) % 24
    return df

df = load_data()
df_simulation = df.sample(frac=1, random_state=42).reset_index(drop=True)

# ============================================================
# FUNGSI GENERATE DATA REALISTIS
# ============================================================
def generate_realistic_data(row, index):
    card_prefix = random.choice(['4532', '4916', '5412', '5234', '3782'])
    card_suffix = str(random.randint(1000, 9999))
    card_number = f"{card_prefix} **** **** {card_suffix}"
    rrn = ''.join(random.choices(string.digits, k=12))
    account = f"ACC{str(index).zfill(8)}"
    merchants_normal = ['Walmart', 'Amazon', 'Target', 'Starbucks',
                        'McDonald', 'Netflix', 'Grab', 'Indomaret']
    merchants_fraud = ['Unknown Merchant', 'XXXONLINE', 'FastCash99',
                       'QuickPay', 'AnonShop', 'DarkStore']
    merchant = random.choice(merchants_fraud) if row['Class'] == 1 else random.choice(merchants_normal)
    return card_number, rrn, account, merchant

# ============================================================
# HEADER + FILTER WAKTU
# ============================================================
header_col1, header_col2 = st.columns([3, 2])

with header_col1:
    st.title("Credit Card Fraud Detection — Live Dashboard")
    st.markdown("Real-time transaction monitoring — by **Fernanda Adytia Pratama**")

with header_col2:
    st.markdown("<br>", unsafe_allow_html=True)
    time_options = ["Semua Data", "15 Menit Terakhir", "1 Jam Terakhir", "Today", "2 Hari Terakhir", "Custom"]
    selected_time = st.selectbox("Filter Rentang Waktu", options=time_options, index=0)

    custom_start = None
    custom_end = None
    if selected_time == "Custom":
        custom_col1, custom_col2 = st.columns(2)
        with custom_col1:
            start_date = st.date_input("Dari Tanggal", value=datetime.now().date())
            start_time_input = st.time_input("Dari Jam", value=datetime.now().replace(hour=0, minute=0).time())
        with custom_col2:
            end_date = st.date_input("Sampai Tanggal", value=datetime.now().date())
            end_time_input = st.time_input("Sampai Jam", value=datetime.now().time())
        custom_start = datetime.combine(start_date, start_time_input)
        custom_end = datetime.combine(end_date, end_time_input)

st.markdown("---")

# ============================================================
# HELPER FILTER WAKTU
# ============================================================
def filter_by_time(df_log):
    if df_log.empty:
        return df_log
    df_log = df_log.copy()
    df_log['Timestamp'] = pd.to_datetime(df_log['Timestamp'])
    now = datetime.now()
    if selected_time == "15 Menit Terakhir":
        cutoff = now - timedelta(minutes=15)
        df_log = df_log[df_log['Timestamp'] >= cutoff]
    elif selected_time == "1 Jam Terakhir":
        cutoff = now - timedelta(hours=1)
        df_log = df_log[df_log['Timestamp'] >= cutoff]
    elif selected_time == "Today":
        cutoff = now.replace(hour=0, minute=0, second=0, microsecond=0)
        df_log = df_log[df_log['Timestamp'] >= cutoff]
    elif selected_time == "2 Hari Terakhir":
        cutoff = now - timedelta(days=2)
        df_log = df_log[df_log['Timestamp'] >= cutoff]
    elif selected_time == "Custom" and custom_start and custom_end:
        df_log = df_log[
            (df_log['Timestamp'] >= custom_start) &
            (df_log['Timestamp'] <= custom_end)
        ]
    df_log['Timestamp'] = df_log['Timestamp'].dt.strftime("%Y-%m-%d %H:%M:%S")
    return df_log

def apply_filters(log_list):
    if not log_list:
        return pd.DataFrame()
    df_log = pd.DataFrame(log_list).iloc[::-1]
    df_log.insert(0, 'No', range(len(log_list), len(log_list) - len(df_log), -1))
    df_log = df_log.head(500)
    if search_rrn:
        df_log['Timestamp'] = df_log['Timestamp'].astype(str)
        df_log = df_log[df_log['RRN'].str.contains(search_rrn, case=False)]
    if search_card:
        df_log = df_log[df_log['Card Number'].str.contains(search_card, case=False)]
    return df_log

# ============================================================
# METRIC CARDS
# ============================================================
col1, col2, col3, col4 = st.columns(4)
metric1 = col1.empty()
metric2 = col2.empty()
metric3 = col3.empty()
metric4 = col4.empty()
st.markdown("---")

# ============================================================
# ALERT
# ============================================================
alert_placeholder = st.empty()
st.markdown("---")

# ============================================================
# SEARCH + TABEL
# ============================================================
search_col1, search_col2 = st.columns(2)
search_rrn = search_col1.text_input("🔍 Cari berdasarkan RRN")
search_card = search_col2.text_input("🔍 Cari berdasarkan Card Number")

st.subheader("Live Transaction Feed")
table_placeholder = st.empty()
st.markdown("---")

# ============================================================
# CHART PLACEHOLDER
# ============================================================
st.subheader("Analisis Realtime")
chart_col1, chart_col2 = st.columns(2)
chart1_placeholder = chart_col1.empty()
chart2_placeholder = chart_col2.empty()

# ============================================================
# FUNGSI UPDATE CHART
# ============================================================
def update_charts(log_list, key_suffix=0):
    if not log_list:
        return

    df_existing = apply_filters(log_list)
    if df_existing.empty:
        return

    # Chart 1 - Pie chart
    class_counts = df_existing['Status'].value_counts().reset_index()
    class_counts.columns = ['Status', 'Count']

    fig1 = px.pie(
        class_counts,
        values='Count',
        names='Status',
        color='Status',
        color_discrete_map={'✅ Normal': '#2ecc71', '🚨 FRAUD': '#e74c3c'},
        title=f'Distribusi Transaksi — Total: {len(df_existing):,}',
        hole=0.45
    )
    fig1.update_traces(textposition='inside', textinfo='percent+label+value')
    fig1.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font_color='white',
        title_font_size=14
    )
    chart1_placeholder.plotly_chart(
        fig1,
        use_container_width=True,
        key=f"chart1_{key_suffix}"
    )

    # Chart 2 - Bar chart per jam
    df_existing2 = df_existing.copy()
    df_existing2['Hour'] = pd.to_datetime(df_existing2['Timestamp']).dt.hour
    hour_group = df_existing2.groupby(['Hour', 'Status']).size().reset_index(name='Count')

    fig2 = px.bar(
        hour_group,
        x='Hour',
        y='Count',
        color='Status',
        color_discrete_map={'✅ Normal': '#2ecc71', '🚨 FRAUD': '#e74c3c'},
        title='Transaksi per Jam (Realtime)',
        barmode='group',
        text='Count'
    )
    fig2.update_traces(textposition='outside')
    fig2.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font_color='white',
        title_font_size=14,
        xaxis=dict(dtick=1)
    )
    chart2_placeholder.plotly_chart(
        fig2,
        use_container_width=True,
        key=f"chart2_{key_suffix}"
    )

# ============================================================
# TAMPILKAN DATA EXISTING
# ============================================================
if st.session_state.transaction_log:
    tc = st.session_state.transaction_count
    fc = st.session_state.fraud_count
    fp = round(fc / tc * 100, 4) if tc > 0 else 0

    metric1.metric("Total Transaksi", f"{tc:,}")
    metric2.metric("Total Fraud", f"{fc:,}")
    metric3.metric("Persentase Fraud", f"{fp}%")
    metric4.metric("Amount Terakhir",
        f"€{st.session_state.transaction_log[-1]['Amount (€)']:.2f}")

    df_log = apply_filters(st.session_state.transaction_log)
    if not df_log.empty:
        table_placeholder.dataframe(df_log, use_container_width=True)
    else:
        table_placeholder.info("Tidak ada data pada rentang waktu yang dipilih.")

    update_charts(st.session_state.transaction_log, key_suffix=0)

# ============================================================
# LOOP LIVE MONITORING
# ============================================================
start_index = st.session_state.last_index

for i in range(start_index, len(df_simulation)):
    row = df_simulation.iloc[i]
    is_fraud = row['Class'] == 1

    card_number, rrn, account, merchant = generate_realistic_data(row, i)

    st.session_state.last_timestamp += timedelta(seconds=random.randint(1, 5))
    timestamp = st.session_state.last_timestamp.strftime("%Y-%m-%d %H:%M:%S")

    st.session_state.transaction_count += 1
    if is_fraud:
        st.session_state.fraud_count += 1

    tc = st.session_state.transaction_count
    fc = st.session_state.fraud_count
    fp = round(fc / tc * 100, 4)

    metric1.metric("Total Transaksi", f"{tc:,}")
    metric2.metric("Total Fraud", f"{fc:,}")
    metric3.metric("Persentase Fraud", f"{fp}%")
    metric4.metric("Amount Terakhir", f"€{row['Amount']:.2f}")

    if is_fraud:
        alert_placeholder.error(
            f"⚠️ FRAUD DETECTED! "
            f"RRN: {rrn} | "
            f"Card: {card_number} | "
            f"Amount: €{row['Amount']:.2f} | "
            f"Merchant: {merchant} | "
            f"Time: {timestamp}"
        )
    else:
        alert_placeholder.success(
            f"✅ Normal | "
            f"RRN: {rrn} | "
            f"Card: {card_number} | "
            f"Amount: €{row['Amount']:.2f} | "
            f"Merchant: {merchant} | "
            f"Time: {timestamp}"
        )

    st.session_state.transaction_log.append({
        'Timestamp': timestamp,
        'RRN': rrn,
        'Card Number': card_number,
        'Account': account,
        'Merchant': merchant,
        'Amount (€)': round(row['Amount'], 2),
        'Status': '🚨 FRAUD' if is_fraud else '✅ Normal'
    })

    st.session_state.last_index = i + 1
    if st.session_state.last_index >= len(df_simulation):
        st.session_state.last_index = 0

    df_log = apply_filters(st.session_state.transaction_log)
    if not df_log.empty:
        table_placeholder.dataframe(df_log, use_container_width=True)
    else:
        table_placeholder.info("Tidak ada data pada rentang waktu yang dipilih.")

    if tc % 3 == 0:
        update_charts(st.session_state.transaction_log, key_suffix=tc)

    time.sleep(1)
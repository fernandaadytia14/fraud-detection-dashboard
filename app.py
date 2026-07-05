import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import warnings

warnings.filterwarnings('ignore')

# Konfigurasi halaman
st.set_page_config(
    page_title="Credit Card Fraud Detection Dashboard",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    .block-container { padding-top: 2rem; }
    h1 { color: #ffffff; font-size: 2.2rem; font-weight: 700; }
    h2 { color: #ffffff; font-size: 1.5rem; font-weight: 600; }
    h3 { color: #ffffff; }
    .stMetric {
        background-color: #1e2130;
        border-radius: 12px;
        padding: 1rem;
        border: 1px solid #2e3250;
    }
    .stMetric label { color: #a0aec0 !important; font-size: 0.85rem; }
    .stMetric div { color: #ffffff !important; font-size: 1.8rem; font-weight: 700; }
    .css-1d391kg { background-color: #1e2130; }
    </style>
""", unsafe_allow_html=True)

# Load data
@st.cache_data
def load_data():
    df = pd.read_csv('creditcard.csv')
    df['Hour'] = (df['Time'] / 3600).astype(int) % 24
    return df

df = load_data()

# ============================================================
# SIDEBAR
# ============================================================
st.sidebar.image("https://img.icons8.com/fluency/96/fraud.png", width=60)
st.sidebar.title("Filter Data")
st.sidebar.markdown("---")

class_filter = st.sidebar.selectbox(
    "Jenis Transaksi",
    options=["All", "Normal (0)", "Fraud (1)"]
)

hour_filter = st.sidebar.slider(
    "Rentang Jam Transaksi",
    min_value=0,
    max_value=23,
    value=(0, 23)
)

amount_filter = st.sidebar.slider(
    "Rentang Nilai Transaksi (€)",
    min_value=float(df['Amount'].min()),
    max_value=float(df['Amount'].max()),
    value=(float(df['Amount'].min()), float(df['Amount'].max()))
)

# Apply filter
df_filtered = df.copy()
if class_filter == "Normal (0)":
    df_filtered = df_filtered[df_filtered['Class'] == 0]
elif class_filter == "Fraud (1)":
    df_filtered = df_filtered[df_filtered['Class'] == 1]

df_filtered = df_filtered[
    (df_filtered['Hour'] >= hour_filter[0]) &
    (df_filtered['Hour'] <= hour_filter[1]) &
    (df_filtered['Amount'] >= amount_filter[0]) &
    (df_filtered['Amount'] <= amount_filter[1])
]

st.sidebar.markdown("---")
st.sidebar.markdown("**Total data:** " + f"{len(df_filtered):,}")
st.sidebar.markdown("**Fraud:** " + f"{df_filtered['Class'].sum():,}")

# ============================================================
# HEADER
# ============================================================
st.title("Credit Card Fraud Detection Dashboard")
st.markdown("Exploratory Data Analysis on Credit Card Transaction Data — by **Fernanda Adytia Pratama**")
st.markdown("---")

# ============================================================
# METRIC CARDS
# ============================================================
col1, col2, col3, col4 = st.columns(4)

total = len(df_filtered)
total_fraud = int(df_filtered['Class'].sum())
fraud_pct = round(df_filtered['Class'].mean() * 100, 4)
max_fraud_amount = df_filtered[df_filtered['Class']==1]['Amount'].max() if total_fraud > 0 else 0

col1.metric("Total Transaksi", f"{total:,}")
col2.metric("Total Fraud", f"{total_fraud:,}")
col3.metric("Persentase Fraud", f"{fraud_pct}%")
col4.metric("Max Amount Fraud", f"€{max_fraud_amount:,.2f}")

st.markdown("---")

# ============================================================
# SECTION 1 - CLASS DISTRIBUTION
# ============================================================
st.subheader("Section 1 — Distribusi Kelas Transaksi")

col1, col2 = st.columns(2)

class_counts = df_filtered['Class'].value_counts().reset_index()
class_counts.columns = ['Class', 'Count']
class_counts['Label'] = class_counts['Class'].map({0: 'Normal', 1: 'Fraud'})

with col1:
    fig = px.bar(
        class_counts,
        x='Label',
        y='Count',
        color='Label',
        color_discrete_map={'Normal': '#2ecc71', 'Fraud': '#e74c3c'},
        title='Jumlah Transaksi Normal vs Fraud',
        text='Count'
    )
    fig.update_traces(texttemplate='%{text:,}', textposition='outside')
    fig.update_layout(
        showlegend=False,
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font_color='white',
        title_font_size=14
    )
    st.plotly_chart(fig, use_container_width=True)

with col2:
    fig = px.pie(
        class_counts,
        values='Count',
        names='Label',
        color='Label',
        color_discrete_map={'Normal': '#2ecc71', 'Fraud': '#e74c3c'},
        title='Proporsi Transaksi Normal vs Fraud',
        hole=0.45
    )
    fig.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font_color='white',
        title_font_size=14
    )
    st.plotly_chart(fig, use_container_width=True)

st.markdown("---")

# ============================================================
# SECTION 2 - ANALISIS WAKTU
# ============================================================
st.subheader("Section 2 — Analisis Pola Waktu Transaksi")

col1, col2 = st.columns(2)

normal_hour = df_filtered[df_filtered['Class']==0]['Hour'].value_counts().sort_index().reset_index()
normal_hour.columns = ['Hour', 'Count']

fraud_hour = df_filtered[df_filtered['Class']==1]['Hour'].value_counts().sort_index().reset_index()
fraud_hour.columns = ['Hour', 'Count']

with col1:
    fig = px.line(
        normal_hour,
        x='Hour',
        y='Count',
        title='Pola Transaksi Normal per Jam',
        markers=True,
        color_discrete_sequence=['#2ecc71']
    )
    fig.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font_color='white',
        title_font_size=14,
        xaxis=dict(dtick=2)
    )
    st.plotly_chart(fig, use_container_width=True)

with col2:
    fig = px.bar(
        fraud_hour,
        x='Hour',
        y='Count',
        title='Pola Transaksi Fraud per Jam',
        color='Count',
        color_continuous_scale='Reds'
    )
    fig.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font_color='white',
        title_font_size=14,
        xaxis=dict(dtick=2)
    )
    st.plotly_chart(fig, use_container_width=True)

st.markdown("---")

# ============================================================
# SECTION 3 - ANALISIS AMOUNT
# ============================================================
st.subheader("Section 3 — Analisis Nilai Transaksi (Amount)")

col1, col2 = st.columns(2)

with col1:
    fig = px.histogram(
        df_filtered,
        x='Amount',
        color='Class',
        color_discrete_map={0: '#2ecc71', 1: '#e74c3c'},
        nbins=100,
        title='Distribusi Amount: Normal vs Fraud',
        barmode='overlay',
        opacity=0.7,
        labels={'Class': 'Kelas'}
    )
    fig.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font_color='white',
        title_font_size=14
    )
    st.plotly_chart(fig, use_container_width=True)

with col2:
    fig = px.box(
        df_filtered,
        x='Class',
        y='Amount',
        color='Class',
        color_discrete_map={0: '#2ecc71', 1: '#e74c3c'},
        title='Boxplot Amount: Normal vs Fraud',
        labels={'Class': 'Kelas (0=Normal, 1=Fraud)'}
    )
    fig.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font_color='white',
        title_font_size=14,
        showlegend=False
    )
    st.plotly_chart(fig, use_container_width=True)

st.markdown("---")

# ============================================================
# SECTION 4 - TOP FITUR V
# ============================================================
st.subheader("Section 4 — Analisis Fitur")

v_features = ['V' + str(i) for i in range(1, 29)]
mean_normal = df[df['Class']==0][v_features].mean()
mean_fraud = df[df['Class']==1][v_features].mean()
mean_diff = abs(mean_normal - mean_fraud).sort_values(ascending=False).reset_index()
mean_diff.columns = ['Feature', 'Difference']
mean_diff['Top5'] = mean_diff['Feature'].isin(mean_diff.head(5)['Feature'])

col1, col2 = st.columns(2)

with col1:
    fig = px.bar(
        mean_diff,
        x='Feature',
        y='Difference',
        color='Top5',
        color_discrete_map={True: '#e74c3c', False: '#3498db'},
        title='Fitur V Paling Membedakan Fraud vs Normal',
    )
    fig.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font_color='white',
        title_font_size=14,
        showlegend=False,
        xaxis=dict(tickangle=45)
    )
    st.plotly_chart(fig, use_container_width=True)

with col2:
    top_features = mean_diff.head(10)['Feature'].tolist() + ['Amount', 'Class']
    top_features = list(dict.fromkeys(top_features))
    corr_matrix = df[top_features].corr().round(2)

    fig = px.imshow(
        corr_matrix,
        color_continuous_scale='RdBu_r',
        zmin=-1,
        zmax=1,
        title='Heatmap Korelasi Top Fitur',
        text_auto=True
    )
    fig.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font_color='white',
        title_font_size=14
    )
    st.plotly_chart(fig, use_container_width=True)

st.markdown("---")

# ============================================================
# FOOTER
# ============================================================
st.markdown("""
    <div style='text-align: center; color: #a0aec0; padding: 1rem;'>
        Credit Card Fraud Detection Dashboard — Fernanda Adytia Pratama | 
        Dataset: Kaggle ULB Credit Card Fraud Detection
    </div>
""", unsafe_allow_html=True)
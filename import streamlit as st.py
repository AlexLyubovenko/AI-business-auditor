import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import json
import os
import sys
import time
from datetime import datetime, timedelta
import base64
from pathlib import Path

# Добавляем путь к корневой директории проекта
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))
from agents.collector import DataCollector
from agents.analyzer import DataAnalyzer
from agents.reporter import ReportGenerator
from agents.amocrm_collector import AmoCRMCollector

# ============================================
# КОНФИГУРАЦИЯ И НАСТРОЙКИ
# ============================================
# Настройки страницы
st.set_page_config(
    page_title="🧠 NeuroPragmat",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ============================================
# КАСТОМНЫЕ CSS СТИЛИ (ФИРМЕННЫЙ СТИЛЬ NEUROPRAGMAT)
# ============================================
def apply_custom_css():
    """Применение кастомных CSS стилей в фирменном стиле NEUROPRAGMAT (тёмная тема, только фирменные цвета)"""
    st.markdown("""
    <style>
    :root {
        --primary-color: #3399FF;      /* RAL 5017 - Traffic Blue */
        --secondary-color: #002163;    /* RAL 5002 - Ultramarine Blue */
        --accent-color: #3399FF;       /* Bright Cyan */
        --dark-color: #212121;         /* RAL 9017 - Traffic Black */
        --surface: #181C22;            /* Тёмная поверхность */
        --text-light: #E8EEF6;         /* Светлый текст */
        --text-dark: #212121;          /* Тёмный текст */
        --muted: #bfc9d9;
        --focus: rgba(51,153,255,0.18);
        --radius: 10px;
        --shadow: 0 6px 18px rgba(0,0,0,0.45);
    }
    html, body, .main .block-container {
        background: var(--dark-color) !important;
        color: var(--text-light) !important;
    }
    * {
        background-color: transparent;
        box-sizing: border-box;
    }
    .main .block-container {
        background: var(--dark-color) !important;
        color: var(--text-light) !important;
        padding-top: 1rem !important;
        padding-bottom: 2rem !important;
    }
    .stText, .stMarkdown, .stMarkdown p, .stMarkdown li, .element-container, .st-emotion-cache-1y4p8pa {
        color: var(--text-light) !important;
        font-family: 'Roboto', 'Open Sans', sans-serif !important;
        font-weight: 400 !important;
        line-height: 1.6 !important;
        font-size: 16px !important;
    }
    h1, h2, h3, h4, h5, h6 {
        font-family: 'Montserrat', 'Inter', sans-serif !important;
        font-weight: 700 !important;
        color: var(--accent-color) !important;
        margin-top: 1.5rem !important;
        margin-bottom: 1rem !important;
    }
    h1 {
        font-size: 3rem !important;
        background: linear-gradient(90deg, var(--primary-color), var(--accent-color)) !important;
        -webkit-background-clip: text !important;
        -webkit-text-fill-color: transparent !important;
        background-clip: text !important;
        border-bottom: 3px solid var(--accent-color) !important;
        padding-bottom: 0.5rem !important;
        margin-top: 0.5rem !important;
    }
    h2 {
        font-size: 2.25rem !important;
        color: var(--primary-color) !important;
        border-left: 4px solid var(--accent-color) !important;
        padding-left: 1rem !important;
        margin-top: 2rem !important;
    }
    h3 {
        font-size: 1.75rem !important;
        color: var(--secondary-color) !important;
        margin-top: 1.5rem !important;
    }
    .card, .panel, .modal, .sheet, .container, .card-root, .app-card, .st-emotion-cache-1jicfl2, .st-emotion-cache-1r4qj8v, .st-emotion-cache-1y4p8pa, div[data-testid="stVerticalBlock"] > div, .content-container {
        background-color: var(--surface) !important;
        color: var(--text-light) !important;
        border-radius: var(--radius);
        box-shadow: var(--shadow);
        border: 1px solid #222a36 !important;
    }
    .stDataFrame, table {
        background: var(--surface) !important;
        color: var(--text-light) !important;
        border-radius: 8px !important;
        border: 1px solid #222a36 !important;
    }
    thead th {
        color: var(--accent-color) !important;
        border-bottom: 1px solid #222a36 !important;
    }
    button, .btn, .stButton > button {
        background-color: var(--primary-color) !important;
        color: #fff !important;
        border: none !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        font-family: 'Montserrat', 'Inter', sans-serif !important;
        box-shadow: 0 4px 6px rgba(51, 153, 255, 0.2) !important;
        transition: all 0.3s ease !important;
    }
    button.secondary, .btn--secondary {
        background-color: var(--secondary-color) !important;
        color: #fff !important;
    }
    button.ghost, .btn--ghost {
        background-color: transparent !important;
        border: 1px solid var(--accent-color) !important;
        color: var(--accent-color) !important;
    }
    button:focus, .btn:focus, .stButton > button:focus {
        outline: none !important;
        box-shadow: 0 0 0 4px var(--focus) !important;
    }
    .stButton > button:hover {
        background: linear-gradient(135deg, var(--accent-color) 0%, var(--primary-color) 100%) !important;
        color: #fff !important;
        transform: translateY(-2px) !important;
        box-shadow: 0 7px 14px rgba(51, 153, 255, 0.3) !important;
    }
    a {
        color: var(--accent-color) !important;
        text-decoration: none !important;
        font-weight: 500 !important;
    }
    a:hover {
        color: var(--primary-color) !important;
        text-decoration: underline !important;
    }
    input, textarea, select, .stTextInput > div > div > input {
        background-color: #23272f !important;
        color: var(--text-light) !important;
        border: 1px solid #222a36 !important;
        border-radius: 8px !important;
        font-family: 'Roboto', sans-serif !important;
        padding: 10px 12px !important;
    }
    input::placeholder, textarea::placeholder {
        color: var(--muted) !important;
    }
    .stFileUploader > div > div {
        border: 2px dashed var(--accent-color) !important;
        border-radius: 8px !important;
        background-color: var(--surface) !important;
        color: var(--text-light) !important;
    }
    .stFileUploader label, .stFileUploader span, .stFileUploader small {
        color: var(--text-light) !important;
    }
    .stRadio label, .stRadio span, .stSelectbox label, .stSelectbox span, .stCheckbox label, .stCheckbox span {
        color: var(--text-light) !important;
        font-family: 'Roboto', sans-serif !important;
        font-weight: 500 !important;
    }
    .stCodeBlock, .stJson {
        background-color: var(--secondary-color) !important;
        color: var(--text-light) !important;
        font-family: 'IBM Plex Mono', 'Courier Prime', monospace !important;
        border-radius: 8px !important;
        border: 1px solid var(--primary-color) !important;
    }
    .streamlit-expanderHeader {
        background-color: var(--surface) !important;
        color: var(--accent-color) !important;
        border: 1px solid #222a36 !important;
        border-radius: 8px !important;
        font-family: 'Montserrat', 'Inter', sans-serif !important;
        font-weight: 600 !important;
    }
    hr {
        border-color: #222a36 !important;
        opacity: 0.5 !important;
        margin: 2rem 0 !important;
    }
    .js-plotly-plot .plotly .modebar {
        background-color: var(--surface) !important;
        border: 1px solid #222a36 !important;
        border-radius: 4px !important;
    }
    .stProgress > div > div > div > div {
        background: linear-gradient(90deg, var(--primary-color), var(--accent-color)) !important;
    }
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, var(--primary-color) 0%, var(--secondary-color) 100%) !important;
    }
    section[data-testid="stSidebar"] h1,
    section[data-testid="stSidebar"] h2,
    section[data-testid="stSidebar"] h3,
    section[data-testid="stSidebar"] h4,
    section[data-testid="stSidebar"] h5,
    section[data-testid="stSidebar"] h6,
    section[data-testid="stSidebar"] p,
    section[data-testid="stSidebar"] span,
    section[data-testid="stSidebar"] div,
    section[data-testid="stSidebar"] label {
        color: var(--text-light) !important;
        font-weight: 500 !important;
    }
    section[data-testid="stSidebar"] h3 {
        background: linear-gradient(90deg, var(--accent-color), #fff) !important;
        -webkit-background-clip: text !important;
        -webkit-text-fill-color: transparent !important;
        background-clip: text !important;
        font-size: 1.3rem !important;
        margin-top: 1rem !important;
        margin-bottom: 0.5rem !important;
    }
    section[data-testid="stSidebar"] .stButton > button {
        background: linear-gradient(135deg, var(--accent-color) 0%, var(--primary-color) 100%) !important;
        color: var(--text-light) !important;
        border-radius: 8px !important;
        padding: 10px 20px !important;
        margin: 5px 0 !important;
        border: 1px solid rgba(255, 255, 255, 0.2) !important;
        width: 100% !important;
    }
    section[data-testid="stSidebar"] .stButton > button:hover {
        background: linear-gradient(135deg, var(--primary-color) 0%, var(--accent-color) 100%) !important;
        transform: translateY(-1px) !important;
        box-shadow: 0 4px 12px rgba(255, 255, 255, 0.2) !important;
    }
    .status-badge {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: 600;
        margin: 2px;
    }
    .status-success {
        background: linear-gradient(135deg, #009A44 0%, #00CC66 100%) !important;
        color: white !important;
        border: 1px solid #009A44;
    }
    .status-warning {
        background: linear-gradient(135deg, #FAD201 0%, #FFE552 100%) !important;
        color: var(--text-dark) !important;
        border: 1px solid #FAD201;
    }
    .status-info {
        background: linear-gradient(135deg, var(--primary-color) 0%, var(--accent-color) 100%) !important;
        color: white !important;
        border: 1px solid var(--primary-color);
    }
    @media (max-width: 768px) {
        h1 { font-size: 2.2rem !important; }
        h2 { font-size: 1.8rem !important; }
        h3 { font-size: 1.4rem !important; }
        .stButton > button { padding: 10px 20px !important; font-size: 14px !important; }
        .main .block-container { padding: 16px !important; }
    }
    </style>
    <link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@400;500;600;700&family=Roboto:wght@300;400;500;600&family=IBM+Plex+Mono&display=swap" rel="stylesheet">
    """, unsafe_allow_html=True)


# ============================================
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# ============================================
def fix_dataframe_types(df):
    """Исправление типов данных для совместимости со Streamlit"""
    if df is None or df.empty:
        return df
    df_fixed = df.copy()
    for col in df_fixed.columns:
        col_lower = str(col).lower()
        # Проверяем, является ли колонка датой
        is_date_column = any(
            keyword in col_lower for keyword in ['дата', 'date', 'время', 'time', 'created', 'updated'])
        if is_date_column:
            try:
                df_fixed[col] = pd.to_datetime(df_fixed[col], errors='coerce', dayfirst=True)
            except Exception as e:
                st.warning(f"Не удалось преобразовать колонку '{col}' в дату: {e}")
        elif df_fixed[col].dtype == 'object':
            try:
                if df_fixed[col].astype(str).str.contains(',').any():
                    df_fixed[col] = df_fixed[col].astype(str).str.replace(',', '.')
                numeric_series = pd.to_numeric(df_fixed[col], errors='coerce')
                if not numeric_series.isna().all():
                    df_fixed[col] = numeric_series
            except:
                pass
    return df_fixed


def convert_df_to_csv(df):
    """Конвертация DataFrame в CSV"""
    return df.to_csv(index=False, encoding='utf-8-sig').encode('utf-8-sig')


def convert_df_to_excel(df):
    """Конвертация DataFrame в Excel"""
    from io import BytesIO
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Data')
    return output.getvalue()


def create_download_button(data, filename, label="📥 Скачать"):
    """Создание кнопки для скачивания файла"""
    if isinstance(data, pd.DataFrame):
        if filename.endswith('.csv'):
            data = convert_df_to_csv(data)
        elif filename.endswith('.xlsx'):
            data = convert_df_to_excel(data)
    b64 = base64.b64encode(data).decode()
    href = f'<a href="data:file/{filename.split(".")[-1]};base64,{b64}" download="{filename}" style="text-decoration: none;">{label}</a>'
    return href


def display_dataframe(df, title="Данные"):
    """Красивое отображение DataFrame в стиле NeuroPragmat"""
    if df is not None and not df.empty:
        st.markdown(
            f'<div class="content-container"><h2 style="color: #002163; border-left: 4px solid #3399FF; padding-left: 16px;">{title}</h2></div>',
            unsafe_allow_html=True)
        st.dataframe(df, use_container_width=True)
        with st.expander("📊 Информация о данных"):
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Строки", len(df))
            with col2:
                st.metric("Колонки", len(df.columns))
            with col3:
                st.metric("Пропуски", df.isnull().sum().sum())
            st.write("**Типы данных:**")
            dtype_info = pd.DataFrame({
                'Колонка': df.columns,
                'Тип': df.dtypes.astype(str),
                'Уникальных': [df[col].nunique() for col in df.columns]
            })
            st.dataframe(dtype_info, use_container_width=True)


# ============================================
# ВКЛАДКА: ЗАГРУЗКА ДАННЫХ - В СТИЛЕ NEUROPRAGMAT
# ============================================
def show_data_upload_tab():
    """Вкладка загрузки данных"""
    st.markdown(
        '<h1 style="background: linear-gradient(90deg, #3399FF, #3399FF); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; border-bottom: 3px solid #3399FF; padding-bottom: 16px;">📤 Загрузка данных</h1>',
        unsafe_allow_html=True)

    tab1, tab2 = st.tabs(["📁 Загрузить файл", "🎯 Примеры данных"])

    with tab1:
        st.markdown(
            '<div class="content-container"><h2 style="color: #002163; border-left: 4px solid #3399FF; padding-left: 16px;">Загрузите свои данные</h2></div>',
            unsafe_allow_html=True)
        uploaded_file = st.file_uploader(
            "Выберите файл (CSV, Excel, JSON, TXT)",
            type=['csv', 'xlsx', 'xls', 'json', 'txt'],
            help="Поддерживаются CSV, Excel, JSON и текстовые файлы"
        )
        if uploaded_file is not None:
            try:
                collector = DataCollector()
                df = collector.load_file(uploaded_file.getvalue(), uploaded_file.name)
                if df is not None and not df.empty:
                    df = fix_dataframe_types(df)
                    st.session_state['uploaded_data'] = df
                    st.session_state['data_source'] = 'file'
                    st.session_state['filename'] = uploaded_file.name
                    st.success(f"✅ Файл '{uploaded_file.name}' успешно загружен!")
                    display_dataframe(df, f"Загруженные данные: {uploaded_file.name}")

                    st.markdown(
                        '<div class="content-container"><h3 style="color: #002163;">📈 Быстрая статистика</h3></div>',
                        unsafe_allow_html=True)
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        numeric_cols = df.select_dtypes(include=[np.number]).columns
                        st.metric("Числовых колонок", len(numeric_cols))
                    with col2:
                        date_cols = df.select_dtypes(include=['datetime64']).columns
                        st.metric("Колонок с датами", len(date_cols))
                    with col3:
                        memory = df.memory_usage(deep=True).sum() / 1024 / 1024
                        st.metric("Объем данных", f"{memory:.2f} МБ")
                else:
                    st.error("❌ Не удалось загрузить данные из файла")
            except Exception as e:
                st.error(f"❌ Ошибка при загрузке файла: {e}")
                st.info("Попробуйте другой файл или используйте примеры данных")

    with tab2:
        st.markdown(
            '<div class="content-container"><h2 style="color: #002163; border-left: 4px solid #3399FF; padding-left: 16px;">Примеры данных для тестирования</h2></div>',
            unsafe_allow_html=True)
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("📊 Финансовые данные", use_container_width=True):
                try:
                    dates = pd.date_range(start='2023-01-01', end='2023-12-31', freq='D')
                    np.random.seed(42)
                    data = {
                        'Дата': dates,
                        'Выручка': np.random.randint(100000, 500000, len(dates)).cumsum() + 1000000,
                        'Расходы': np.random.randint(50000, 200000, len(dates)).cumsum() + 500000,
                        'Прибыль': np.random.randint(30000, 150000, len(dates)).cumsum() + 300000,
                        'Клиенты': np.random.randint(10, 100, len(dates)),
                        'Средний_чек': np.random.randint(5000, 20000, len(dates))
                    }
                    df = pd.DataFrame(data)
                    df['Прибыль'] = df['Выручка'] - df['Расходы']
                    st.session_state['uploaded_data'] = df
                    st.session_state['data_source'] = 'demo_finance'
                    st.session_state['filename'] = 'demo_finance.csv'
                    st.success("✅ Загружены демо финансовые данные!")
                    display_dataframe(df, "Финансовые данные (демо)")
                except Exception as e:
                    st.error(f"Ошибка: {e}")
        with col2:
            if st.button("🛒 Данные продаж", use_container_width=True):
                try:
                    dates = pd.date_range(start='2023-01-01', periods=365, freq='D')
                    np.random.seed(123)
                    data = {
                        'Дата': dates,
                        'Товар': np.random.choice(['Товар A', 'Товар B', 'Товар C', 'Товар D'], 365),
                        'Количество': np.random.randint(1, 50, 365),
                        'Цена': np.random.randint(1000, 10000, 365),
                        'Регион': np.random.choice(['Москва', 'СПб', 'Новосибирск', 'Екатеринбург'], 365),
                        'Канал_продаж': np.random.choice(['Сайт', 'Маркетплейс', 'Розница', 'Опт'], 365)
                    }
                    df = pd.DataFrame(data)
                    df['Выручка'] = df['Количество'] * df['Цена']
                    st.session_state['uploaded_data'] = df
                    st.session_state['data_source'] = 'demo_sales'
                    st.session_state['filename'] = 'demo_sales.csv'
                    st.success("✅ Загружены демо данные продаж!")
                    display_dataframe(df, "Данные продаж (демо)")
                except Exception as e:
                    st.error(f"Ошибка: {e}")
        with col3:
            if st.button("📈 Бизнес метрики", use_container_width=True):
                try:
                    months = pd.date_range(start='2023-01-01', periods=12, freq='M')
                    data = {
                        'Месяц': months,
                        'Выручка': [1500000, 1650000, 1420000, 1780000, 1950000, 2100000,
                                    2250000, 2400000, 2550000, 2700000, 2850000, 3000000],
                        'Расходы': [900000, 950000, 920000, 980000, 1050000, 1100000,
                                    1150000, 1200000, 1250000, 1300000, 1350000, 1400000],
                        'Новые_клиенты': [120, 135, 110, 150, 165, 180, 195, 210, 225, 240, 255, 270],
                        'LTV': [25000, 25500, 24800, 26000, 26500, 27000, 27500, 28000, 28500, 29000, 29500, 30000],
                        'CAC': [8000, 8200, 8100, 8300, 8400, 8500, 8600, 8700, 8800, 8900, 9000, 9100]
                    }
                    df = pd.DataFrame(data)
                    df['Прибыль'] = df['Выручка'] - df['Расходы']
                    df['ROI'] = (df['Прибыль'] / df['Расходы'] * 100).round(2)
                    st.session_state['uploaded_data'] = df
                    st.session_state['data_source'] = 'demo_metrics'
                    st.session_state['filename'] = 'demo_metrics.csv'
                    st.success("✅ Загружены демо бизнес метрики!")
                    display_dataframe(df, "Бизнес метрики (демо)")
                except Exception as e:
                    st.error(f"Ошибка: {e}")

    if 'uploaded_data' in st.session_state and st.session_state['uploaded_data'] is not None:
        st.divider()
        st.markdown('<div class="content-container"><h3 style="color: #002163;">🚀 Действия с данными</h3></div>',
                    unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        with col1:
            if st.button("📊 Перейти к анализу", type="primary", use_container_width=True):
                st.session_state['current_tab'] = "Анализ данных"
                st.rerun()
        with col2:
            df = st.session_state['uploaded_data']
            filename = st.session_state.get('filename', 'data.csv')
            csv = convert_df_to_csv(df)
            st.download_button(
                label="📥 Скачать данные",
                data=csv,
                file_name=filename,
                mime="text/csv",
                use_container_width=True
            )


# ============================================
# ВКЛАДКА: АНАЛИЗ ДАННЫХ - В СТИЛЕ NEUROPRAGMAT
# ============================================
def show_analysis_tab():
    """Вкладка анализа данных"""
    st.markdown(
        '<h1 style="background: linear-gradient(90deg, #3399FF, #3399FF); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; border-bottom: 3px solid #3399FF; padding-bottom: 16px;">🔍 Анализ данных</h1>',
        unsafe_allow_html=True)

    if 'uploaded_data' not in st.session_state or st.session_state['uploaded_data'] is None:
        st.warning("⚠️ Сначала загрузите данные во вкладке 'Загрузка данных'")
        if st.button("📤 Перейти к загрузке данных"):
            st.session_state['current_tab'] = "Загрузка данных"
            st.rerun()
        return

    df = st.session_state['uploaded_data']
    df = fix_dataframe_types(df)

    display_dataframe(df, "Ваши данные")

    analysis_type = st.radio(
        "Выберите тип анализа:",
        ["📈 Базовый анализ", "🤖 AI-анализ с GPT"],
        horizontal=True
    )

    if analysis_type == "📈 Базовый анализ":
        show_basic_analysis(df)
    else:
        show_ai_analysis(df)


def show_basic_analysis(df):
    """Базовый анализ данных"""
    st.markdown(
        '<div class="content-container"><h2 style="color: #002163; border-left: 4px solid #3399FF; padding-left: 16px;">📊 Базовый анализ</h2></div>',
        unsafe_allow_html=True)

    with st.spinner("Анализируем данные..."):
        try:
            analyzer = DataAnalyzer()
            results = analyzer.analyze(df)
            if results:
                st.success("✅ Анализ завершен!")

                st.markdown('<div class="content-container"><h3 style="color: #002163;">📈 Основные метрики</h3></div>',
                            unsafe_allow_html=True)
                if 'metrics' in results:
                    metrics = results['metrics']
                    cols = st.columns(4)
                    metric_keys = list(metrics.keys())[:4]
                    for idx, key in enumerate(metric_keys):
                        with cols[idx]:
                            value = metrics[key]
                            if isinstance(value, (int, float)):
                                if abs(value) >= 1000000:
                                    display_value = f"{value / 1000000:.2f}M"
                                elif abs(value) >= 1000:
                                    display_value = f"{value / 1000:.1f}K"
                                else:
                                    display_value = f"{value:.0f}"
                                if 'Percent' in key or '%' in key:
                                    display_value = f"{value:.1f}%"
                                st.metric(key.replace('_', ' '), display_value)

                if 'trends' in results and results['trends']:
                    st.markdown(
                        '<div class="content-container"><h3 style="color: #002163;">📈 Обнаруженные тренды</h3></div>',
                        unsafe_allow_html=True)
                    trends_df = pd.DataFrame(results['trends'])
                    st.dataframe(trends_df, use_container_width=True)

                    if len(trends_df) > 0:
                        fig = go.Figure()
                        colors = ['#3399FF', '#002163', '#3399FF', '#009A44', '#FAD201']
                        for idx, row in trends_df.iterrows():
                            fig.add_trace(go.Bar(
                                x=[row['Метрика']],
                                y=[abs(row['Наклон'])],
                                name=row['Направление'],
                                marker_color=colors[idx % len(colors)],
                                text=[f"{row['Направление']}<br>Наклон: {row['Наклон']:.2f}"],
                                textposition='auto'
                            ))
                        fig.update_layout(
                            title="Сила трендов по метрикам",
                            yaxis_title="Абсолютное значение наклона",
                            showlegend=False,
                            height=400,
                            plot_bgcolor='white',
                            paper_bgcolor='white',
                            font=dict(color='#212121')
                        )
                        st.plotly_chart(fig, use_container_width=True)

                if 'recommendations' in results and results['recommendations']:
                    st.markdown('<div class="content-container"><h3 style="color: #002163;">💡 Рекомендации</h3></div>',
                                unsafe_allow_html=True)
                    for rec in results['recommendations']:
                        with st.container():
                            st.markdown(f"**{rec.get('type', 'Рекомендация')}:** {rec.get('text', '')}")
                            if 'priority' in rec:
                                priority = rec['priority']
                                if priority == 'high':
                                    st.markdown('<div class="ai-warning">Высокий приоритет</div>',
                                                unsafe_allow_html=True)
                                elif priority == 'medium':
                                    st.markdown('<div class="ai-insight">Средний приоритет</div>',
                                                unsafe_allow_html=True)

                st.markdown(
                    '<div class="content-container"><h3 style="color: #002163;">📊 Визуализация данных</h3></div>',
                    unsafe_allow_html=True)
                numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
                date_cols = df.select_dtypes(include=['datetime64']).columns.tolist()

                if len(date_cols) > 0 and len(numeric_cols) > 0:
                    date_col = date_cols[0]
                    value_col = numeric_cols[0] if len(numeric_cols) > 0 else None
                    if value_col:
                        fig = px.line(df, x=date_col, y=value_col,
                                      title=f"Тренд {value_col} по времени")
                        fig.update_layout(
                            plot_bgcolor='white',
                            paper_bgcolor='white',
                            font=dict(color='#212121')
                        )
                        st.plotly_chart(fig, use_container_width=True)

                if len(numeric_cols) > 0:
                    selected_col = st.selectbox("Выберите колонку для распределения:", numeric_cols)
                    if selected_col:
                        fig = px.histogram(df, x=selected_col,
                                           title=f"Распределение {selected_col}")
                        fig.update_layout(
                            plot_bgcolor='white',
                            paper_bgcolor='white',
                            font=dict(color='#212121')
                        )
                        st.plotly_chart(fig, use_container_width=True)
            else:
                st.error("❌ Не удалось выполнить анализ")
        except Exception as e:
            st.error(f"❌ Ошибка при анализе: {e}")
            st.info("Попробуйте другой тип анализа или проверьте данные")


def show_ai_analysis(df):
    """AI анализ с помощью GPT"""
    st.markdown(
        '<div class="content-container"><h2 style="color: #002163; border-left: 4px solid #3399FF; padding-left: 16px;">🤖 AI-анализ с GPT</h2></div>',
        unsafe_allow_html=True)

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key or api_key == "your_openai_api_key_here":
        st.warning("""
        ⚠️ OpenAI API ключ не настроен!
        Для использования AI-анализа:
        1. Получите API ключ на platform.openai.com
        2. Добавьте в .env файл: `OPENAI_API_KEY=ваш_ключ_здесь`
        3. Перезапустите приложение
        """)
        if st.button("🔄 Использовать базовый анализ вместо AI"):
            show_basic_analysis(df)
        return

    with st.expander("⚙️ Настройки AI-анализа"):
        model_choice = st.selectbox(
            "Модель GPT:",
            ["gpt-3.5-turbo", "gpt-4", "gpt-4-turbo-preview"],
            index=0
        )
        analysis_depth = st.select_slider(
            "Глубина анализа:",
            options=["Базовый", "Стандартный", "Детальный", "Экспертный"],
            value="Стандартный"
        )

    if st.button("🚀 Запустить AI-анализ", type="primary"):
        with st.spinner("🤖 AI анализирует данные... Это может занять до 30 секунд"):
            try:
                analyzer = DataAnalyzer()
                basic_results = analyzer.analyze(df)
                ai_analysis = analyzer.gpt_analysis(
                    data_summary=analyzer.get_data_summary(df),
                    trends=basic_results.get('trends', []) if basic_results else [],
                    financial_metrics=basic_results.get('metrics', {}) if basic_results else {}
                )
                if ai_analysis:
                    st.success("✅ AI-анализ завершен!")
                    display_ai_analysis(ai_analysis)
                    st.session_state['last_ai_analysis'] = ai_analysis
                    st.session_state['last_basic_analysis'] = basic_results
                    if st.button("📄 Создать отчет на основе AI-анализа"):
                        st.session_state['current_tab'] = "Отчеты"
                        st.rerun()
                else:
                    st.error("❌ AI не смог проанализировать данные")
                    st.info("Попробуйте базовый анализ или проверьте подключение к интернету")
            except Exception as e:
                st.error(f"❌ Ошибка AI-анализа: {e}")
                st.info("Попробуйте позже или используйте базовый анализ")


def display_ai_analysis(analysis_text):
    """Красивое отображение AI анализа в стиле NeuroPragmat"""
    if not analysis_text:
        st.warning("❌ AI анализ не содержит данных")
        return
    sections = analysis_text.split('\n## ')
    if len(sections) > 1:
        first_section = sections[0]
        other_sections = sections[1:]
        st.markdown(f"""
        <div class="ai-analysis-section">
        <h2 style="color: white; margin-top: 0;">🎯 AI Анализ бизнеса</h2>
        {first_section}
        </div>
        """, unsafe_allow_html=True)
        for section in other_sections:
            if section.strip():
                lines = section.strip().split('\n')
                if lines:
                    title = lines[0]
                    content = '\n'.join(lines[1:]) if len(lines) > 1 else ""
                    title_lower = title.lower()
                    title_upper = title.upper()
                    if any(word in title_lower for word in ['рекомендац', 'совет', 'что делать', 'рекомендации']):
                        css_class = "ai-recommendation"
                    elif any(word in title_lower for word in ['риск', 'проблем', 'опасност', 'угроз']):
                        css_class = "ai-warning"
                    elif any(word in title_lower for word in ['вывод', 'итог', 'заключен', 'резюме']):
                        css_class = "ai-analysis-section"
                    else:
                        css_class = "ai-insight"
                    # ИСПРАВЛЕНО: Убраны звездочки и обратные кавычки из текста предупреждения.
                    if "ВНИМАНИЕ" in title_upper or "ПРЕДУПРЕЖДЕНИЕ" in title_upper:
                        content_cleaned = content.replace("*", "").replace("`", "")
                        st.markdown(f"""
                        <div class="{css_class}">
                        <h3 style="color: white; margin-top: 0;">{title}</h3>
                        {content_cleaned}
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        st.markdown(f"""
                        <div class="{css_class}">
                        <h3 style="color: white; margin-top: 0;">{title}</h3>
                        {content}
                        </div>
                        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div class="ai-analysis-section">
        <h2 style="color: white; margin-top: 0;">🤖 Анализ искусственного интеллекта</h2>
        {analysis_text}
        </div>
        """, unsafe_allow_html=True)


# ============================================
# ВКЛАДКА: AMOCRM - В СТИЛЕ NEUROPRAGMAT
# ============================================
def show_amocrm_tab():
    """Вкладка AmoCRM интеграции"""
    st.markdown(
        '<h1 style="background: linear-gradient(90deg, #3399FF, #3399FF); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; border-bottom: 3px solid #3399FF; padding-bottom: 16px;">🔗 AmoCRM Интеграция</h1>',
        unsafe_allow_html=True)

    st.info("""
    🎮 **Демо-режим активен** - используются тестовые данные
    Для реального подключения к AmoCRM:
    1. Получите ключи API в вашем AmoCRM
    2. Добавьте их в .env файл
    3. Отключите демо-режим
    """)

    demo_mode = st.checkbox(
        "🎮 Использовать демо-режим",
        value=True,
        help="Использовать тестовые данные без реального подключения к AmoCRM"
    )

    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("📊 Загрузить сделки", type="primary", use_container_width=True):
            load_amocrm_data(demo_mode, data_type="leads")
    with col2:
        if st.button("👥 Загрузить контакты", use_container_width=True):
            load_amocrm_data(demo_mode, data_type="contacts")
    with col3:
        if st.button("🏢 Загрузить компании", use_container_width=True):
            load_amocrm_data(demo_mode, data_type="companies")

    if 'amocrm_data' in st.session_state and st.session_state['amocrm_data']:
        display_amocrm_data(st.session_state['amocrm_data'])

    if not demo_mode:
        st.divider()
        st.markdown('<div class="content-container"><h3 style="color: #002163;">🔧 Настройки подключения</h3></div>',
                    unsafe_allow_html=True)
        if st.button("🔄 Проверить подключение к AmoCRM"):
            check_amocrm_connection()


def load_amocrm_data(demo_mode=True, data_type="leads"):
    """Загрузка данных из AmoCRM"""
    with st.spinner(f"Загружаем {data_type} из AmoCRM..."):
        try:
            from agents.amocrm_collector import AmoCRMCollector
            collector = AmoCRMCollector()
            if demo_mode:
                st.info("🔶 Используется демо-режим AmoCRM")
                data = collector.get_demo_data(data_type)
            else:
                if not collector.check_connection():
                    st.error("❌ Не настроено подключение к AmoCRM")
                    st.info("Добавьте AMOCRM_ACCESS_TOKEN в .env или используйте демо-режим")
                    return
                if data_type == "leads":
                    data = collector.get_leads()
                elif data_type == "contacts":
                    data = collector.get_contacts()
                elif data_type == "companies":
                    data = collector.get_companies()
                else:
                    data = collector.get_demo_data(data_type)
            if data:
                st.session_state['amocrm_data'] = {
                    'type': data_type,
                    'data': data,
                    'demo_mode': demo_mode
                }
                st.success(f"✅ Успешно загружено: {len(data) if isinstance(data, list) else 1} записей")
            else:
                st.warning(f"⚠️ Не удалось загрузить {data_type}")
        except Exception as e:
            st.error(f"❌ Ошибка при загрузке: {e}")
            st.info("Используйте демо-режим для тестирования")


def check_amocrm_connection():
    """Проверка подключения к AmoCRM"""
    with st.spinner("Проверяем подключение..."):
        try:
            from agents.amocrm_collector import AmoCRMCollector
            collector = AmoCRMCollector()
            is_connected = collector.check_connection()
            if is_connected:
                st.success("✅ Подключение к AmoCRM работает!")
                account_info = collector.get_account_info()
                if account_info:
                    st.json(account_info)
            else:
                st.error("❌ Не удалось подключиться к AmoCRM")
                st.info("""
                Проверьте:
                1. AMOCRM_ACCESS_TOKEN в .env файле
                2. Срок действия токена (действителен 24 часа)
                3. Правильность AMOCRM_SUBDOMAIN
                """)
        except Exception as e:
            st.error(f"❌ Ошибка проверки: {e}")


def display_amocrm_data(amocrm_data):
    """Отображение данных из AmoCRM"""
    data_type = amocrm_data['type']
    data = amocrm_data['data']
    demo_mode = amocrm_data.get('demo_mode', True)
    st.divider()

    if demo_mode:
        st.info(f"📋 **Демо-данные:** {data_type} ({len(data) if isinstance(data, list) else 1} записей)")
    else:
        st.success(f"📋 **Реальные данные из AmoCRM:** {data_type}")

    if isinstance(data, list) and len(data) > 0:
        df = pd.DataFrame(data)
        if 'custom_fields_values' in df.columns:
            df = df.drop(columns=['custom_fields_values'])
        if '_embedded' in df.columns:
            df = df.drop(columns=['_embedded'])

        if data_type == "leads":
            show_amocrm_metrics(df, "сделок")
        elif data_type == "contacts":
            show_amocrm_metrics(df, "контактов")
        elif data_type == "companies":
            show_amocrm_metrics(df, "компаний")

        st.dataframe(df, use_container_width=True)

        if data_type == "leads" and 'price' in df.columns and len(df) > 1:
            st.markdown('<div class="content-container"><h3 style="color: #002163;">📊 Анализ сделок</h3></div>',
                        unsafe_allow_html=True)
            col1, col2 = st.columns(2)
            with col1:
                fig = px.histogram(df, x='price',
                                   title="Распределение сделок по сумме",
                                   labels={'price': 'Сумма сделки'})
                fig.update_layout(
                    plot_bgcolor='white',
                    paper_bgcolor='white',
                    font=dict(color='#212121')
                )
                st.plotly_chart(fig, use_container_width=True)
            with col2:
                if len(df) > 5:
                    top_leads = df.nlargest(5, 'price')
                    fig = px.bar(top_leads, x='name', y='price',
                                 title="Топ-5 сделок по сумме",
                                 labels={'name': 'Сделка', 'price': 'Сумма'})
                    fig.update_layout(
                        plot_bgcolor='white',
                        paper_bgcolor='white',
                        font=dict(color='#212121')
                    )
                    st.plotly_chart(fig, use_container_width=True)
    elif isinstance(data, dict):
        st.json(data)
    else:
        st.write("Данные:", data)


def show_amocrm_metrics(df, data_type):
    """Показ метрик для AmoCRM данных"""
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric(f"Всего {data_type}", len(df))
    with col2:
        if 'price' in df.columns:
            total = df['price'].sum()
            st.metric("Общая сумма", f"{total:,.0f} ₽")
        else:
            st.metric("Записей", len(df))
    with col3:
        if 'created_at' in df.columns:
            try:
                df['created_at'] = pd.to_datetime(df['created_at'])
                recent = len(df[df['created_at'] > pd.Timestamp.now() - pd.Timedelta(days=30)])
                st.metric("За 30 дней", recent)
            except:
                st.metric("Данные", "Обновлены")
        else:
            st.metric("Статус", "Загружено")
    with col4:
        if 'status_id' in df.columns:
            unique_statuses = df['status_id'].nunique()
            st.metric("Уникальных статусов", unique_statuses)
        else:
            st.metric("Колонок", len(df.columns))


# ============================================
# ВКЛАДКА: ВИЗУАЛИЗАЦИИ - В СТИЛЕ NEUROPRAGMAT
# ============================================
def show_visualizations_tab():
    """Вкладка визуализаций"""
    st.markdown(
        '<h1 style="background: linear-gradient(90deg, #3399FF, #3399FF); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; border-bottom: 3px solid #3399FF; padding-bottom: 16px;">📊 Визуализации</h1>',
        unsafe_allow_html=True)

    if 'uploaded_data' not in st.session_state or st.session_state['uploaded_data'] is None:
        st.warning("⚠️ Сначала загрузите данные для визуализации")
        if st.button("📤 Перейти к загрузке данных"):
            st.session_state['current_tab'] = "Загрузка данных"
            st.rerun()
        return

    df = st.session_state['uploaded_data']
    df = fix_dataframe_types(df)

    viz_type = st.selectbox(
        "Выберите тип визуализации:",
        ["📈 Линейный график", "📊 Столбчатая диаграмма", "🍩 Круговая диаграмма",
         "📦 Диаграмма рассеяния", "📈 Тепловая карта", "📊 Box plot"]
    )

    with st.expander("🔧 Настройки данных"):
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        all_cols = df.columns.tolist()
        if len(numeric_cols) >= 2:
            x_col = st.selectbox("Ось X:", all_cols, index=0)
            y_col = st.selectbox("Ось Y:", numeric_cols, index=min(1, len(numeric_cols) - 1))
            if 'Дата' in all_cols or 'дата' in [c.lower() for c in all_cols]:
                date_col = st.selectbox("Колонка с датой:",
                                        [c for c in all_cols if 'дата' in c.lower() or 'date' in c.lower()],
                                        index=0)
                df_sorted = df.sort_values(date_col)
            else:
                df_sorted = df
            color_col = st.selectbox("Колонка для цвета:", ["Нет"] + all_cols, index=0)
            if color_col == "Нет":
                color_col = None
        else:
            st.warning("Нужно хотя бы 2 числовые колонки для визуализации")
            return

    if st.button("🚀 Создать визуализацию", type="primary"):
        try:
            if viz_type == "📈 Линейный график":
                if color_col:
                    fig = px.line(df_sorted, x=x_col, y=y_col, color=color_col,
                                  title=f"{y_col} по {x_col}")
                else:
                    fig = px.line(df_sorted, x=x_col, y=y_col,
                                  title=f"{y_col} по {x_col}")
            elif viz_type == "📊 Столбчатая диаграмма":
                if color_col:
                    fig = px.bar(df_sorted, x=x_col, y=y_col, color=color_col,
                                 title=f"{y_col} по {x_col}")
                else:
                    fig = px.bar(df_sorted, x=x_col, y=y_col,
                                 title=f"{y_col} по {x_col}")
            elif viz_type == "🍩 Круговая диаграмма":
                fig = px.pie(df, names=x_col, values=y_col,
                             title=f"Распределение {y_col} по {x_col}")
            elif viz_type == "📦 Диаграмма рассеяния":
                if color_col:
                    fig = px.scatter(df_sorted, x=x_col, y=y_col, color=color_col,
                                     title=f"Диаграмма рассеяния: {y_col} vs {x_col}")
                else:
                    fig = px.scatter(df_sorted, x=x_col, y=y_col,
                                     title=f"Диаграмма рассеяния: {y_col} vs {x_col}")
            elif viz_type == "📈 Тепловая карта":
                corr_df = df[numeric_cols].corr()
                fig = px.imshow(corr_df,
                                title="Тепловая карта корреляций",
                                labels=dict(x="Колонки", y="Колонки", color="Корреляция"))
            elif viz_type == "📊 Box plot":
                fig = px.box(df, x=x_col, y=y_col,
                             title=f"Box plot: {y_col} по {x_col}")

            fig.update_layout(
                template="plotly_white",
                height=500,
                showlegend=True,
                font=dict(size=12, color='#212121'),
                plot_bgcolor='white',
                paper_bgcolor='white'
            )

            st.plotly_chart(fig, use_container_width=True)

            col1, col2 = st.columns(2)
            with col1:
                if st.button("💾 Сохранить как PNG"):
                    try:
                        img_bytes = fig.to_image(format="png", width=1200, height=600)
                        st.download_button(
                            label="📥 Скачать PNG",
                            data=img_bytes,
                            file_name="visualization.png",
                            mime="image/png"
                        )
                    except Exception as e:
                        st.error(f"Ошибка сохранения: {e}")
                        st.info("Установите пакет: pip install -U kaleido")
            with col2:
                if st.button("📊 Сохранить как HTML"):
                    html = fig.to_html()
                    st.download_button(
                        label="📥 Скачать HTML",
                        data=html,
                        file_name="visualization.html",
                        mime="text/html"
                    )
        except Exception as e:
            st.error(f"❌ Ошибка создания визуализации: {e}")


# ============================================
# ВКЛАДКА: ОТЧЕТЫ - В СТИЛЕ NEUROPRAGMAT
# ============================================
def show_reports_tab():
    """Вкладка отчетов"""
    st.markdown(
        '<h1 style="background: linear-gradient(90deg, #3399FF, #3399FF); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; border-bottom: 3px solid #3399FF; padding-bottom: 16px;">📄 Отчеты</h1>',
        unsafe_allow_html=True)

    has_data = 'uploaded_data' in st.session_state and st.session_state['uploaded_data'] is not None
    has_analysis = 'last_basic_analysis' in st.session_state or 'last_ai_analysis' in st.session_state

    if not has_data:
        st.warning("⚠️ Нет данных для отчета. Сначала загрузите данные.")
        return

    report_type = st.selectbox(
        "Тип отчета:",
        ["📊 Краткий отчет", "📈 Детальный анализ", "🤖 AI отчет", "📋 Полный бизнес-отчет"]
    )

    with st.expander("⚙️ Настройки отчета"):
        include_visualizations = st.checkbox("Включить графики", value=True)
        include_recommendations = st.checkbox("Включить рекомендации", value=True)
        include_data_summary = st.checkbox("Включить сводку данных", value=True)

    if st.button("🚀 Создать отчет", type="primary"):
        with st.spinner("Создаем отчет..."):
            try:
                df = st.session_state['uploaded_data']
                report_data = {
                    'data': df,
                    'report_type': report_type,
                    'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    'filename': st.session_state.get('filename', 'data.csv')
                }

                if 'last_basic_analysis' in st.session_state:
                    report_data['basic_analysis'] = st.session_state['last_basic_analysis']
                if 'last_ai_analysis' in st.session_state:
                    report_data['ai_analysis'] = st.session_state['last_ai_analysis']

                reporter = ReportGenerator()
                report = reporter.generate_report(report_data)

                if report:
                    st.success("✅ Отчет создан!")
                    st.markdown(
                        '<div class="content-container"><h3 style="color: #002163;">👁️ Предпросмотр отчета</h3></div>',
                        unsafe_allow_html=True)

                    # ======= ЯРКИЙ БЛОК ДЛЯ СКАЧИВАНИЯ ОТЧЁТА =======
                    st.markdown(
                        '<div style="background:linear-gradient(90deg,#3399FF 0%,#002163 100%);padding:18px 0 18px 0;text-align:center;border-radius:12px;margin-bottom:18px;box-shadow:0 2px 12px #00216340;">'
                        '<span style="color:#fff;font-size:1.2rem;font-weight:700;">⬇️ СКАЧАЙТЕ ОТЧЁТ:</span>'
                        '</div>',
                        unsafe_allow_html=True)
                    if 'markdown' in report:
                        md_data = report['markdown']
                        if isinstance(md_data, str):
                            md_data = md_data.encode("utf-8")
                        st.download_button(
                            label="📝 Скачать Markdown (.md)",
                            data=md_data,
                            file_name="neuropragmat_report.md",
                            mime="text/markdown",
                            use_container_width=True
                        )
                    elif 'pdf' in report:
                        pdf_data = report['pdf']
                        st.download_button(
                            label="📄 Скачать PDF (.pdf)",
                            data=pdf_data,
                            file_name="neuropragmat_report.pdf",
                            mime="application/pdf",
                            use_container_width=True
                        )

                    # ======= СТАРЫЙ БЛОК ЭКСПОРТА (оставлен для выбора других форматов) =======
                    st.markdown(
                        '<div class="content-container"><h3 style="color: #002163;">📤 Экспорт отчета</h3></div>',
                        unsafe_allow_html=True)
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        if 'markdown' in report:
                            md_data = report['markdown']
                            if isinstance(md_data, str):
                                md_data = md_data.encode("utf-8")
                            st.download_button(
                                label="📝 Markdown (.md)",
                                data=md_data,
                                file_name="neuropragmat_report.md",
                                mime="text/markdown",
                                use_container_width=True
                            )
                    with col2:
                        if 'json' in report:
                            json_data = report['json']
                            if isinstance(json_data, str):
                                json_data = json_data.encode("utf-8")
                            st.download_button(
                                label="🔤 JSON (.json)",
                                data=json_data,
                                file_name="neuropragmat_report.json",
                                mime="application/json",
                                use_container_width=True
                            )
                    with col3:
                        if 'html' in report:
                            html_data = report['html']
                            if isinstance(html_data, str):
                                html_data = html_data.encode("utf-8")
                            st.download_button(
                                label="🌐 HTML (.html)",
                                data=html_data,
                                file_name="neuropragmat_report.html",
                                mime="text/html",
                                use_container_width=True
                            )
                    with col4:
                        if 'pdf' in report:
                            pdf_data = report['pdf']
                            st.download_button(
                                label="📄 PDF (.pdf)",
                                data=pdf_data,
                                file_name="neuropragmat_report.pdf",
                                mime="application/pdf",
                                use_container_width=True
                            )

                    st.session_state['last_report'] = report
                else:
                    st.error("❌ Не удалось создать отчет")
            except Exception as e:
                st.error(f"❌ Ошибка создания отчета: {e}")


# ============================================
# ОСНОВНАЯ ФУНКЦИЯ - В СТИЛЕ NEUROPRAGMAT
# ============================================
def main():
    """Основная функция приложения"""
    # Применяем CSS стили
    apply_custom_css()

    # Инициализация session_state
    if 'current_tab' not in st.session_state:
        st.session_state['current_tab'] = "Загрузка данных"
    current_tab = st.session_state.get('current_tab', "Загрузка данных")

    # ====== НОВЫЙ ЕДИНЫЙ ВЕРХНИЙ БЛОК (КАК НА СКРИНШОТЕ 1) ======
    st.markdown("""
    <div style="width:100%; background:linear-gradient(90deg,#002163 0%,#3399FF 100%); border-radius:18px; box-shadow:0 4px 24px #00216340; padding:48px 0 32px 0; text-align:center; margin-bottom:32px; position:relative;">
        <h1 style="color:#fff; font-family:Montserrat,Inter,sans-serif; font-weight:900; font-size:3.2rem; margin:0; letter-spacing:2px; text-shadow:0 4px 24px #002163cc, 0 1px 0 #3399FF; filter:none;">🧠 <span style='color:#fff; font-weight:900; text-shadow:0 4px 24px #002163cc, 0 1px 0 #3399FF;'>NeuroPragmat</span></h1>
        <hr style="border:0; border-top:2px solid #3399FF; width:80%; margin:24px auto 24px auto; opacity:0.5;" />
        <h2 style="color:#fff; font-family:Montserrat,Inter,sans-serif; font-weight:700; font-size:1.6rem; margin:0; text-shadow:0 2px 8px #00216380;">Интеллектуальный анализ бизнес-данных и автоматизация отчетности</h2>
    </div>
    """, unsafe_allow_html=True)

    # Сайдбар с навигацией
    with st.sidebar:
        st.markdown(
            '<h2 style="color: white; background: linear-gradient(90deg, #3399FF, white); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;">Навигация</h2>',
            unsafe_allow_html=True)
        # Кнопки навигации
        tabs = {
            "📤 Загрузка данных": "Загрузка данных",
            "🔍 Анализ данных": "Анализ данных",
            "🔗 AmoCRM": "AmoCRM",
            "📊 Визуализации": "Визуализации",
            "📄 Отчеты": "Отчеты"
        }
        for icon, tab_name in tabs.items():
            if st.button(icon, key=f"btn_{tab_name}", use_container_width=True):
                st.session_state['current_tab'] = tab_name
                st.rerun()
        st.divider()
        # Информация о системе
        st.markdown(
            '<h3 style="color: white; background: linear-gradient(90deg, #3399FF, white); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;">ℹ️ Информация</h3>',
            unsafe_allow_html=True)
        st.write(f"**Текущая вкладка:** {st.session_state['current_tab']}")
        if 'uploaded_data' in st.session_state and st.session_state['uploaded_data'] is not None:
            df = st.session_state['uploaded_data']
            st.write(f"**Данные:** {len(df)} строк, {len(df.columns)} колонок")
        # Статус подключений
        st.markdown(
            '<h3 style="color: white; background: linear-gradient(90deg, #3399FF, white); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;">🔗 Подключения</h3>',
            unsafe_allow_html=True)
        api_key = os.getenv("OPENAI_API_KEY")
        if api_key and api_key != "your_openai_api_key_here":
            st.markdown('<span class="status-badge status-success">✅ OpenAI API</span>', unsafe_allow_html=True)
        else:
            st.markdown('<span class="status-badge status-warning">⚠️ OpenAI API</span>', unsafe_allow_html=True)
        amocrm_token = os.getenv("AMOCRM_ACCESS_TOKEN")
        if amocrm_token and amocrm_token != "your_amocrm_access_token_here":
            st.markdown('<span class="status-badge status-success">✅ AmoCRM</span>', unsafe_allow_html=True)
        else:
            st.markdown('<span class="status-badge status-info">🎮 AmoCRM (демо)</span>', unsafe_allow_html=True)
        st.divider()
        # Быстрые действия
        st.markdown(
            '<h3 style="color: white; background: linear-gradient(90deg, #3399FF, white); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;">⚡ Быстрые действия</h3>',
            unsafe_allow_html=True)
        if st.button("🔄 Перезагрузить приложение", use_container_width=True):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.experimental_set_query_params()  # сброс параметров
            st.success("Приложение перезагружено! Обновите страницу вручную (F5)")
        if st.button("🧹 Очистить все данные", use_container_width=True):
            keys_to_clear = ['uploaded_data', 'last_ai_analysis', 'last_basic_analysis', 'amocrm_data', 'last_report']
            for key in keys_to_clear:
                if key in st.session_state:
                    del st.session_state[key]
            st.success("Данные очищены!")
            st.rerun()

    # Основное содержимое
    current_tab = st.session_state['current_tab']
    if current_tab == "Загрузка данных":
        show_data_upload_tab()
    elif current_tab == "Анализ данных":
        show_analysis_tab()
    elif current_tab == "AmoCRM":
        show_amocrm_tab()
    elif current_tab == "Визуализации":
        show_visualizations_tab()
    elif current_tab == "Отчеты":
        show_reports_tab()

    # ====== УБРАНО: Старый заголовок и старый нижний блок ======
    # Полностью удалены оба старых блока, оставлен только один новый вверху.

    # Футер
    st.divider()
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("""
        <div style="text-align: center; color: #002163; font-size: 0.9rem; font-family: 'Roboto', sans-serif; padding: 16px; background: linear-gradient(135deg, rgba(0, 85, 160, 0.08) 0%, rgba(51, 153, 255, 0.08) 100%); border-radius: 8px; border: 1px solid rgba(0, 85, 160, 0.15);">
            <p><strong style="color: #0055A0;">🧠 NeuroPragmat v1.0</strong> | 📊 Интеллектуальный анализ бизнес-данных</p>
            <p style="margin-top: 8px;">Для вопросов и поддержки: <a href="mailto:support@neuropragmat.com" style="color: #3399FF; text-decoration: none; font-weight: 500;">support@neuropragmat.com</a></p>
        </div>
        """, unsafe_allow_html=True)


# ============================================
# ЗАПУСК ПРИЛОЖЕНИЯ
# ============================================
if __name__ == "__main__":
    from dotenv import load_dotenv

    load_dotenv()
    main()
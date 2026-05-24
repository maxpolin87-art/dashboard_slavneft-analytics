import pandas as pd
import streamlit as st
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
from PIL import Image
import os

st.set_page_config(
    page_title="Аналитика и прогноз выполнения договоров ПАО \"Славнефть-Мегионнефтегаз\"", 
    layout="wide"
)

# === ЛОГОТИП В ПРАВОМ ВЕРХНЕМ УГЛУ ===
col1, col2 = st.columns([6, 1])
with col1:
    st.title("📊 Аналитика и прогноз выполнения договоров ПАО \"Славнефть-Мегионнефтегаз\"")
with col2:
    # Пытаемся загрузить логотип
    logo_path = "logo.jpg"
    if os.path.exists(logo_path):
        try:
            logo = Image.open(logo_path)
            st.image(logo, width=80)
        except:
            st.markdown("🏗️")
    else:
        st.markdown("🏗️")

# === ЗАГРУЗКА ДАННЫХ ===
@st.cache_data
def load_data():
    df = pd.read_csv('parsed_data.csv', parse_dates=['Дата_документа'])
    return df

df = load_data()
df['Договор'] = df['Договор'].replace({'Договор 110': 'ДРЛ_1 110', 'Договор 111': 'ДРЛ_1 111'})
df['Тип_работ'] = df['Тип_работ'].replace({'Мобилизация': 'Мобилизация/Переезд', 'Переезд': 'Мобилизация/Переезд'})

# === ПЛАНОВЫЕ ДАННЫЕ ===
plan_data = {
    'ДРЛ_1 110': {
        'сумма_план': 2746781054.35,
        'скважин_план': 48,
        'дата_план': pd.Timestamp('2025-12-31')
    },
    'ДРЛ_1 111': {
        'сумма_план': 2746781054.35,
        'скважин_план': 48,
        'дата_план': pd.Timestamp('2026-12-31')
    }
}
total_plan_sum = plan_data['ДРЛ_1 110']['сумма_план'] + plan_data['ДРЛ_1 111']['сумма_план']
total_plan_wells = plan_data['ДРЛ_1 110']['скважин_план'] + plan_data['ДРЛ_1 111']['скважин_план']

# === БОКОВАЯ ПАНЕЛЬ ===
st.sidebar.header("🔍 Фильтры")
contract_filter = st.sidebar.selectbox("Договор", ['Все договоры', 'ДРЛ_1 110', 'ДРЛ_1 111'])

min_date = df['Дата_документа'].min().date()
max_date = df['Дата_документа'].max().date()
date_range = st.sidebar.date_input("Период", value=[min_date, max_date], min_value=min_date, max_value=max_date)

st.sidebar.header("⚙️ Прогноз")
teams_110 = st.sidebar.slider("Бригад на договоре 110", 0, 4, 1)
teams_111 = st.sidebar.slider("Бригад на договоре 111", 0, 4, 1)

# === ПРИМЕНЕНИЕ ФИЛЬТРОВ ===
filtered_df = df.copy()
if contract_filter != 'Все договоры':
    filtered_df = filtered_df[filtered_df['Договор'] == contract_filter]
if len(date_range) == 2:
    start_date, end_date = date_range
    filtered_df = filtered_df[
        (filtered_df['Дата_документа'].dt.date >= start_date) &
        (filtered_df['Дата_документа'].dt.date <= end_date)
    ]

# ============================================
# === БЛОК 1: ПРОГНОЗ ОКОНЧАНИЯ (3 СЦЕНАРИЯ) ===
# ============================================
st.header("🎯 ПРОГНОЗ ОКОНЧАНИЯ ДОГОВОРОВ")

# Текущее состояние
wells_done_110 = df[df['Договор'] == 'ДРЛ_1 110']['Скважина'].nunique()
wells_done_111 = df[df['Договор'] == 'ДРЛ_1 111']['Скважина'].nunique()
wells_remains_110 = max(0, 48 - wells_done_110)
wells_remains_111 = max(0, 48 - wells_done_111)

sum_done_110 = df[df['Договор'] == 'ДРЛ_1 110']['Сумма'].sum()
sum_done_111 = df[df['Договор'] == 'ДРЛ_1 111']['Сумма'].sum()
remains_sum_110 = plan_data['ДРЛ_1 110']['сумма_план'] - sum_done_110
remains_sum_111 = plan_data['ДРЛ_1 111']['сумма_план'] - sum_done_111

# Флаг просрочки по дате
today = datetime.now()
is_overdue_110 = today > plan_data['ДРЛ_1 110']['дата_план'] and (wells_remains_110 > 0 or remains_sum_110 > 0)
is_overdue_111 = today > plan_data['ДРЛ_1 111']['дата_план'] and (wells_remains_111 > 0 or remains_sum_111 > 0)

col1, col2, col3, col4 = st.columns(4)

if is_overdue_110:
    col1.metric("Договор 110: осталось скважин", wells_remains_110, delta="⚠️ ПРОСРОЧЕН", delta_color="inverse")
    col2.metric("Договор 110: осталось по деньгам", f"{remains_sum_110:,.0f} ₽", delta="⚠️ ПРОСРОЧЕН", delta_color="inverse")
else:
    col1.metric("Договор 110: осталось скважин", wells_remains_110)
    col2.metric("Договор 110: осталось по деньгам", f"{remains_sum_110:,.0f} ₽")

if is_overdue_111:
    col3.metric("Договор 111: осталось скважин", wells_remains_111, delta="⚠️ ПРОСРОЧЕН", delta_color="inverse")
    col4.metric("Договор 111: осталось по деньгам", f"{remains_sum_111:,.0f} ₽", delta="⚠️ ПРОСРОЧЕН", delta_color="inverse")
else:
    col3.metric("Договор 111: осталось скважин", wells_remains_111)
    col4.metric("Договор 111: осталось по деньгам", f"{remains_sum_111:,.0f} ₽")

# Предупреждение о просрочке
if is_overdue_110:
    st.error(f"🚨 **Договор 110 ПРОСРОЧЕН!** Плановая дата окончания: {plan_data['ДРЛ_1 110']['дата_план'].strftime('%d.%m.%Y')}. Текущая дата: {today.strftime('%d.%m.%Y')}. Договор не завершён по скважинам и/или деньгам.")
if is_overdue_111:
    st.error(f"🚨 **Договор 111 ПРОСРОЧЕН!** Плановая дата окончания: {plan_data['ДРЛ_1 111']['дата_план'].strftime('%d.%m.%Y')}. Текущая дата: {today.strftime('%d.%m.%Y')}. Договор не завершён по скважинам и/или деньгам.")

# Расчёт средней стоимости одной скважины и средней дневной выручки на 1 бригаду
avg_well_cost_110 = df[df['Договор'] == 'ДРЛ_1 110'].groupby('Скважина')['Сумма'].sum().mean()
avg_well_cost_111 = df[df['Договор'] == 'ДРЛ_1 111'].groupby('Скважина')['Сумма'].sum().mean()
avg_days_per_well = 30  # среднее время на одну скважину (в днях)

# Средняя дневная выручка на 1 бригаду
daily_rate_110 = avg_well_cost_110 / avg_days_per_well if avg_well_cost_110 > 0 else 0
daily_rate_111 = avg_well_cost_111 / avg_days_per_well if avg_well_cost_111 > 0 else 0

# Прогноз по каждому договору
for contract, teams, remains_sum, avg_well_cost, daily_rate in [
    ('ДРЛ_1 110', teams_110, remains_sum_110, avg_well_cost_110, daily_rate_110),
    ('ДРЛ_1 111', teams_111, remains_sum_111, avg_well_cost_111, daily_rate_111)
]:
    st.subheader(f"📋 {contract}")
    
    wells_remains = wells_remains_110 if contract == 'ДРЛ_1 110' else wells_remains_111
    plan_date = plan_data[contract]['дата_план']
    is_overdue = is_overdue_110 if contract == 'ДРЛ_1 110' else is_overdue_111
    
    # Прогноз по скважинам
    if wells_remains > 0 and teams > 0:
        days_by_wells = (wells_remains * avg_days_per_well) / teams
        date_by_wells = datetime.now() + timedelta(days=days_by_wells)
    else:
        days_by_wells = None
        date_by_wells = None
    
    # Прогноз по деньгам (с учётом бригад)
    if remains_sum > 0 and daily_rate > 0 and teams > 0:
        days_by_money = remains_sum / (daily_rate * teams)
        date_by_money = datetime.now() + timedelta(days=days_by_money)
    else:
        days_by_money = None
        date_by_money = None
    
    col1, col2, col3 = st.columns(3)
    
    if is_overdue:
        col1.markdown(f"**⚠️ ПРОСРОЧЕН**")
        col2.markdown(f"**⚠️ ПРОСРОЧЕН**")
    
    if date_by_wells:
        color_wells = "🟢" if date_by_wells <= plan_date else "🔴"
        col1.metric(f"{color_wells} По скважинам", date_by_wells.strftime('%d.%m.%Y'))
    else:
        col1.metric("По скважинам", "✅ Завершён" if wells_remains == 0 else "⚠️ Нет бригад")
    
    if date_by_money:
        color_money = "🟢" if date_by_money <= plan_date else "🔴"
        col2.metric(f"{color_money} По деньгам", date_by_money.strftime('%d.%m.%Y'))
    else:
        col2.metric("По деньгам", "✅ Завершён" if remains_sum <= 0 else "⚠️ Нет данных")
    
    col3.metric("📅 Плановая дата", plan_date.strftime('%d.%m.%Y'))
    
    # Ограничивающий фактор
    if date_by_wells and date_by_money:
        if date_by_wells > date_by_money and date_by_wells > plan_date:
            st.warning(f"⚠️ Ограничивающий фактор: **СКВАЖИНЫ** (прогноз {date_by_wells.strftime('%d.%m.%Y')})")
        elif date_by_money > date_by_wells and date_by_money > plan_date:
            st.warning(f"⚠️ Ограничивающий фактор: **ДЕНЬГИ** (прогноз {date_by_money.strftime('%d.%m.%Y')})")
        elif date_by_wells <= plan_date and date_by_money <= plan_date:
            st.success("✅ Оба прогноза укладываются в план")
        else:
            st.info("📊 Прогноз требует анализа")
    elif date_by_wells and not date_by_money:
        if date_by_wells > plan_date:
            st.warning(f"⚠️ Ограничивающий фактор: **СКВАЖИНЫ** (прогноз {date_by_wells.strftime('%d.%m.%Y')})")
        else:
            st.success("✅ Прогноз по скважинам укладывается в план")
    elif not date_by_wells and date_by_money:
        if date_by_money > plan_date:
            st.warning(f"⚠️ Ограничивающий фактор: **ДЕНЬГИ** (прогноз {date_by_money.strftime('%d.%m.%Y')})")
        else:
            st.success("✅ Прогноз по деньгам укладывается в план")

# Прогноз по проекту с перетоком
st.subheader("🔄 ПРОГНОЗ ПО ПРОЕКТУ (оба договора)")
if wells_remains_110 > 0 and wells_remains_111 > 0:
    # Средняя стоимость скважины по проекту и дневная ставка
    avg_well_cost_project = (avg_well_cost_110 + avg_well_cost_111) / 2
    daily_rate_project = avg_well_cost_project / avg_days_per_well
    
    time_110 = (wells_remains_110 * avg_days_per_well) / teams_110 if teams_110 > 0 else float('inf')
    time_111 = (wells_remains_111 * avg_days_per_well) / teams_111 if teams_111 > 0 else float('inf')
    
    # Прогноз по деньгам для проекта
    remains_sum_total = remains_sum_110 + remains_sum_111
    total_teams = teams_110 + teams_111
    if remains_sum_total > 0 and daily_rate_project > 0 and total_teams > 0:
        days_by_money_project = remains_sum_total / (daily_rate_project * total_teams)
        date_by_money_project = datetime.now() + timedelta(days=days_by_money_project)
    else:
        days_by_money_project = float('inf')
        date_by_money_project = None
    
    if time_110 < time_111:
        total_time = time_110 + max(0, (wells_remains_111 * avg_days_per_well - teams_111 * time_110) / (teams_111 + teams_110))
        st.info(f"📌 Договор 110 завершится первым → {teams_110} бригад перейдут на 111")
    else:
        total_time = time_111 + max(0, (wells_remains_110 * avg_days_per_well - teams_110 * time_111) / (teams_110 + teams_111))
        st.info(f"📌 Договор 111 завершится первым → {teams_111} бригад перейдут на 110")
    
    forecast_date = datetime.now() + timedelta(days=total_time)
    
    col1, col2, col3 = st.columns(3)
    col1.metric("⏱️ По скважинам", f"{total_time:.0f} дней")
    if date_by_money_project:
        col2.metric("💰 По деньгам", f"{days_by_money_project:.0f} дней")
    else:
        col2.metric("💰 По деньгам", "Нет данных")
    col3.metric("📅 Прогнозная дата", forecast_date.strftime('%d.%m.%Y'))
    
    if forecast_date > pd.Timestamp('2026-12-31'):
        st.warning(f"⚠️ Прогноз ({forecast_date.strftime('%d.%m.%Y')}) позже плановой даты (31.12.2026)")
    else:
        st.success(f"✅ Прогноз укладывается в план до 31.12.2026")

elif wells_remains_110 > 0:
    total_time = (wells_remains_110 * avg_days_per_well) / teams_110 if teams_110 > 0 else float('inf')
    forecast_date = datetime.now() + timedelta(days=total_time)
    if is_overdue_110:
        st.error(f"🚨 Договор 110 ПРОСРОЧЕН! Прогноз завершения: {forecast_date.strftime('%d.%m.%Y')}")
    else:
        st.metric("Прогноз завершения договора 110", forecast_date.strftime('%d.%m.%Y'))
    
elif wells_remains_111 > 0:
    total_time = (wells_remains_111 * avg_days_per_well) / teams_111 if teams_111 > 0 else float('inf')
    forecast_date = datetime.now() + timedelta(days=total_time)
    if is_overdue_111:
        st.error(f"🚨 Договор 111 ПРОСРОЧЕН! Прогноз завершения: {forecast_date.strftime('%d.%m.%Y')}")
    else:
        st.metric("Прогноз завершения договора 111", forecast_date.strftime('%d.%m.%Y'))
    
else:
    st.success("🎉 ВСЕ ДОГОВОРЫ ВЫПОЛНЕНЫ!")

# ============================================
# === БЛОК 2: СТАТИСТИКА ПО СКВАЖИНАМ ===
# ============================================
st.header("📊 СТАТИСТИКА ПО СКВАЖИНАМ")

# Средняя стоимость скважины
well_cost = filtered_df.groupby('Скважина')['Сумма'].sum().reset_index()
if not well_cost.empty:
    avg_well_cost = well_cost['Сумма'].mean()
    median_well_cost = well_cost['Сумма'].median()
    
    col1, col2 = st.columns(2)
    col1.metric("💰 Средняя стоимость скважины", f"{avg_well_cost:,.0f} ₽")
    col2.metric("📊 Медианная стоимость скважины", f"{median_well_cost:,.0f} ₽")
else:
    st.info("Нет данных по скважинам")

# Стоимость по типам работ
st.subheader("💰 Средняя стоимость по типам работ")
stage_avg_cost = filtered_df.groupby('Тип_работ')['Сумма'].mean().reset_index()
if not stage_avg_cost.empty:
    stage_avg_cost.columns = ['Тип работ', 'Средняя стоимость']
    stage_avg_cost['Средняя стоимость'] = stage_avg_cost['Средняя стоимость'].apply(lambda x: f"{x:,.0f} ₽")
    st.dataframe(stage_avg_cost, use_container_width=True, hide_index=True)

# Динамика стоимости скважины по годам
if 'Дата_документа' in filtered_df.columns and not filtered_df.empty:
    filtered_df['Год'] = filtered_df['Дата_документа'].dt.year
    yearly_well_cost = filtered_df.groupby(['Год', 'Скважина'])['Сумма'].sum().reset_index()
    yearly_avg_cost = yearly_well_cost.groupby('Год')['Сумма'].mean().reset_index()
    
    if not yearly_avg_cost.empty:
        fig2 = px.bar(yearly_avg_cost, x='Год', y='Сумма', 
                      title="📈 Динамика средней стоимости скважины по годам",
                      labels={'Сумма': 'Средняя стоимость (₽)', 'Год': 'Год'},
                      color_discrete_sequence=['#2E86AB'])
        st.plotly_chart(fig2, use_container_width=True)

# Количество закрытых скважин по месяцам
st.subheader("📅 Количество закрытых скважин по месяцам")
if not filtered_df.empty:
    wells_by_month = filtered_df.groupby([filtered_df['Дата_документа'].dt.to_period('M').dt.start_time, 'Скважина']).size().reset_index()
    wells_by_month = wells_by_month.groupby('Дата_документа')['Скважина'].nunique().reset_index()
    wells_by_month.columns = ['Месяц', 'Количество скважин']
    
    if not wells_by_month.empty:
        fig3 = px.bar(wells_by_month, x='Месяц', y='Количество скважин', 
                      title="Количество закрытых скважин по месяцам",
                      color_discrete_sequence=['#A23B72'])
        st.plotly_chart(fig3, use_container_width=True)

# ============================================
# === БЛОК 3: АНАЛИТИКА ПО ЭТАПАМ ===
# ============================================
st.header("⏱️ АНАЛИТИКА ПО ЭТАПАМ")

# Расчёт разниц между этапами
def calculate_stage_gaps(df_data):
    if df_data.empty:
        return pd.DataFrame()
    
    well_stages = df_data.groupby(['Скважина', 'Тип_работ'])['Дата_документа'].min().reset_index()
    pivot = well_stages.pivot(index='Скважина', columns='Тип_работ', values='Дата_документа').reset_index()
    
    gaps = []
    for _, row in pivot.iterrows():
        well = row['Скважина']
        
        if pd.notna(row.get('Мобилизация/Переезд')) and pd.notna(row.get('Монтаж')):
            gaps.append({'Скважина': well, 'От': 'Мобилизация/Переезд', 'До': 'Монтаж', 'Дней': (row['Монтаж'] - row['Мобилизация/Переезд']).days})
        if pd.notna(row.get('Монтаж')) and pd.notna(row.get('Бурение')):
            gaps.append({'Скважина': well, 'От': 'Монтаж', 'До': 'Бурение', 'Дней': (row['Бурение'] - row['Монтаж']).days})
        if pd.notna(row.get('Бурение')) and pd.notna(row.get('Демонтаж')):
            gaps.append({'Скважина': well, 'От': 'Бурение', 'До': 'Демонтаж', 'Дней': (row['Демонтаж'] - row['Бурение']).days})
    
    return pd.DataFrame(gaps)

gaps_df = calculate_stage_gaps(filtered_df)

if not gaps_df.empty:
    # Сводная статистика по разницам
    st.subheader("📊 Сводная статистика разрывов между этапами")
    summary = gaps_df.groupby(['От', 'До'])['Дней'].agg(['mean', 'max', 'min', 'count']).reset_index()
    summary.columns = ['От', 'До', 'Средняя (дней)', 'Максимальная (дней)', 'Минимальная (дней)', 'Количество']
    summary['Средняя (дней)'] = summary['Средняя (дней)'].round(1)
    st.dataframe(summary, use_container_width=True, hide_index=True)
    
    # Топ проблемных скважин
    st.subheader("⚠️ ТОП-5 ПРОБЛЕМНЫХ СКВАЖИН (по суммарной задержке)")
    problem_wells = gaps_df[gaps_df['Дней'] > 0].groupby('Скважина')['Дней'].sum().reset_index()
    problem_wells.columns = ['Скважина', 'Суммарная задержка (дней)']
    problem_wells = problem_wells.sort_values('Суммарная задержка (дней)', ascending=False).head(5)
    
    if not problem_wells.empty:
        st.dataframe(problem_wells, use_container_width=True, hide_index=True)
    else:
        st.success("✅ Нет проблемных скважин")
else:
    st.info("Нет данных для анализа разрывов между этапами")

# ============================================
# === БЛОК 4: ОБЩАЯ СТАТИСТИКА ===
# ============================================
st.header("📊 ОБЩАЯ СТАТИСТИКА")

if not filtered_df.empty:
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Всего записей", len(filtered_df))
    c2.metric("Всего скважин", filtered_df['Скважина'].nunique())
    c3.metric("Общая сумма", f"{filtered_df['Сумма'].sum():,.0f} ₽")
    c4.metric("Период", f"{filtered_df['Дата_документа'].min().strftime('%d.%m.%Y')} - {filtered_df['Дата_документа'].max().strftime('%d.%m.%Y')}")
else:
    st.info("Нет данных для отображения статистики")

st.success("✅ Дашборд загружен! Используйте фильтры слева для анализа.")
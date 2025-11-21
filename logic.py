import pandas as pd
import numpy as np
import os
import logging
from datetime import datetime

# Отримуємо логер для цього модуля
logger = logging.getLogger(__name__)

def generate_power_load_data(start_year: int, end_year: int, random_seed: int = None) -> pd.DataFrame:
    """
    PRO VERSION: Генерує дані з урахуванням економічних трендів та аномалій.
    Використовує векторизацію NumPy для максимальної швидкодії.
    """
    logger.info(f"Початок генерації PRO даних: {start_year}-{end_year}, Seed: {random_seed}")
    
    if random_seed is not None:
        np.random.seed(random_seed)
    
    start_date = f'{start_year}-01-01'
    end_date = f'{end_year}-12-31'
    date_range = pd.date_range(start=start_date, end=end_date, freq='h')
    n = len(date_range)

    # 1. Базова векторизація часу
    day_of_year = date_range.dayofyear.to_numpy()
    hour = date_range.hour.to_numpy()
    day_of_week = date_range.dayofweek.to_numpy()
    
    # --- ФІЗИЧНА МОДЕЛЬ ---
    
    # Температура (з імітацією глобального потепління: +0.05 градуса щороку)
    year_offset = date_range.year.to_numpy() - start_year
    climate_trend = year_offset * 0.05
    
    base_temp = 10 + 25 * np.sin(2 * np.pi * (day_of_year - 15) / 365) + climate_trend
    daily_temp_variation = 8 * np.sin(2 * np.pi * (hour - 6) / 24)
    temp_noise = np.random.normal(0, 2, n)
    
    temperature_c = base_temp + daily_temp_variation + temp_noise
    
    # Базове навантаження (Добовий цикл)
    base_load = 4000 + 800 * np.sin(2 * np.pi * hour / 24)
    
    # Економічний тренд (Ріст споживання ~1.5% на рік)
    growth_factor = 1 + (year_offset * 0.015)
    
    # Температурний ефект (Опалення / Кондиціювання)
    temp_effect = np.zeros(n)
    mask_cold = temperature_c < 0
    temp_effect[mask_cold] = 300 * (0 - temperature_c[mask_cold]) / 15
    mask_hot = temperature_c > 25
    temp_effect[mask_hot] = 200 * (temperature_c[mask_hot] - 25) / 10
    
    # Коефіцієнти (Сезонність + Тип дня)
    seasonal_factor = 1 + 0.15 * np.sin(2 * np.pi * (day_of_year - 15) / 365)
    weekday_factor = np.where(day_of_week >= 5, 0.85, 1.0)
    
    # Формула навантаження
    load_mw = (base_load + temp_effect) * seasonal_factor * weekday_factor * growth_factor
    
    # Додаємо шум
    random_noise = np.random.normal(0, 120, n)
    load_mw += random_noise
    
    # Пікові години (Ранковий та вечірній пік)
    mask_peaks = ((hour >= 7) & (hour <= 10)) | ((hour >= 17) & (hour <= 20))
    load_mw[mask_peaks] *= 1.12
    
    # --- АНОМАЛІЇ (Імітація аварій/викидів) ---
    # 0.1% шанс аномалії (приблизно 8-10 годин на рік)
    anomaly_indices = np.random.choice(n, size=int(n * 0.001), replace=False)
    # Аномалії можуть бути падінням (аварія) або стрибком
    load_mw[anomaly_indices] *= np.random.uniform(0.6, 1.4, size=len(anomaly_indices))

    # Свята (Україна)
    holidays_list = []
    for y in range(start_year, end_year + 1):
        holidays_list.extend([
            f'{y}-01-01', f'{y}-01-07', f'{y}-03-08', 
            f'{y}-05-01', f'{y}-05-09', f'{y}-06-28',
            f'{y}-08-24', f'{y}-10-14', f'{y}-12-25'
        ])
    
    holiday_dates = pd.to_datetime(holidays_list)
    is_holiday = date_range.normalize().isin(holiday_dates).astype(int)
    
    # Генерація (Вітер) та Потужність станцій
    wind_mps = np.random.gamma(2, 1.5, n)
    power_base = load_mw + 1000 # Резерв потужності
    capacity_mw = power_base + np.random.normal(0, 80, n)
    
    # Кліпінг (Захист від нереальних значень) та оптимізація типів (float32)
    df = pd.DataFrame({
        'timestamp': date_range,
        'load_mw': np.clip(load_mw, 2000, 8000).astype(np.float32).round(1),
        'temperature_c': np.clip(temperature_c, -35, 45).astype(np.float32).round(1),
        'wind_mps': np.clip(wind_mps, 0, 35).astype(np.float32).round(1),
        'is_holiday': is_holiday.astype(np.int8),
        'capacity_mw': np.clip(capacity_mw, 3000, 9000).astype(np.float32).round(1),
        'year': date_range.year.astype(np.int16)
    })
    
    logger.info("Генерація завершена успішно.")
    return df

def prepare_data(df: pd.DataFrame) -> pd.DataFrame:
    """Збагачує DataFrame додатковими полями для аналізу."""
    logger.info("Підготовка даних (Data Enrichment)...")
    
    df['date'] = df['timestamp'].dt.date
    df['month'] = df['timestamp'].dt.month
    
    month_names_ua = {
        1: 'Січень', 2: 'Лютий', 3: 'Березень', 4: 'Квітень',
        5: 'Травень', 6: 'Червень', 7: 'Липень', 8: 'Серпень',
        9: 'Вересень', 10: 'Жовтень', 11: 'Листопад', 12: 'Грудень'
    }
    df['month_name'] = df['month'].map(month_names_ua)
    
    month_order = {name: i for i, name in month_names_ua.items()}
    df['month_order'] = df['month_name'].map(month_order)
    
    df['quarter'] = df['timestamp'].dt.quarter
    df['hour'] = df['timestamp'].dt.hour
    
    df['day_type'] = np.where(df['is_holiday'] == 1, 'Свято', 'Робочий')
    
    day_names_ua = {
        'Monday': 'Понеділок', 'Tuesday': 'Вівторок', 'Wednesday': 'Середа',
        'Thursday': 'Четвер', 'Friday': 'П\'ятниця', 'Saturday': 'Субота', 'Sunday': 'Неділя'
    }
    df['day_of_week'] = df['timestamp'].dt.day_name().map(day_names_ua)
    
    return df

def create_csv_reports(df: pd.DataFrame, output_dir: str, random_mode: str):
    """
    Створює професійний Excel звіт (.xlsx) та резервний CSV.
    """
    logger.info(f"Початок експорту звітів у: {output_dir}")
    output_path = os.path.abspath(output_dir)
    
    if not os.path.exists(output_path):
        os.makedirs(output_path)
    
    timestamp_str = datetime.now().strftime("%Y%m%d_%H%M")
    
    # 1. Збереження Raw Data (CSV) - Технічний файл
    csv_file = os.path.join(output_path, "raw_data.csv")
    df.to_csv(csv_file, index=False, encoding='utf-8')
    logger.info(f"CSV збережено: {csv_file}")

    # 2. Підготовка зведених таблиць (Analytics)
    daily_pivot = pd.pivot_table(
        df, values='load_mw', index=[df['timestamp'].dt.date, 'month_name'],
        columns='day_type', aggfunc='mean'
    ).round(1)
    
    monthly_pivot = pd.pivot_table(
        df, values='load_mw', index='month_name',
        columns='year', aggfunc='mean'
    ).round(1)

    # 3. Генерація Excel звіту (Business Report)
    excel_file = os.path.join(output_path, f"Report_{timestamp_str}.xlsx")
    
    try:
        # Використовуємо openpyxl для запису
        with pd.ExcelWriter(excel_file, engine='openpyxl') as writer:
            # Аркуш 1: Зведена статистика
            daily_pivot.to_excel(writer, sheet_name='Денна статистика')
            monthly_pivot.to_excel(writer, sheet_name='Місячна статистика')
            
            # Аркуш 2: Метадані (Audit Trail)
            info_df = pd.DataFrame({
                'Параметр': ['Час генерації', 'Період', 'Режим', 'Записів оброблено', 'Середнє навантаження'],
                'Значення': [
                    datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    f"{df['year'].min()} - {df['year'].max()}",
                    random_mode,
                    len(df),
                    f"{df['load_mw'].mean():.2f} МВт"
                ]
            })
            info_df.to_excel(writer, sheet_name='INFO', index=False)
            
            # Авто-підбір ширини колонок (Visual Polish)
            for sheet_name in writer.sheets:
                sheet = writer.sheets[sheet_name]
                for column in sheet.columns:
                    try:
                        length = max(len(str(cell.value)) for cell in column)
                        sheet.column_dimensions[column[0].column_letter].width = min(length + 2, 50)
                    except: pass
            
        logger.info(f"Excel звіт успішно створено: {excel_file}")
        
    except ImportError:
        logger.warning("Модуль openpyxl не встановлено. Excel звіт пропущено (тільки CSV).")
    except Exception as e:
        logger.error(f"Помилка при створенні Excel: {e}")

    # 4. Короткий текстовий звіт
    create_text_report(df, output_path, random_mode)

def create_text_report(df, output_path, random_mode):
    report_file = os.path.join(output_path, "summary.txt")
    
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write("ЗВІТ З АНАЛІЗУ НАВАНТАЖЕННЯ ЕНЕРГОСИСТЕМИ\n")
        f.write("=" * 50 + "\n\n")
        f.write(f"Дата: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
        f.write(f"Період: {df['year'].min()} - {df['year'].max()}\n")
        f.write(f"Режим: {random_mode}\n\n")
        f.write(f"Середнє навантаження: {df['load_mw'].mean():.1f} МВт\n")
        f.write(f"Макс. навантаження: {df['load_mw'].max():.1f} МВт\n")
        
    logger.info("Текстовий звіт створено.")

def get_random_mode_description(mode):
    return "Детермінований (Seed 42)" if mode == "reproducible" else "Стохастичний (Випадковий)"

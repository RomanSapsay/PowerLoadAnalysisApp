import pandas as pd
import numpy as np
import os
from datetime import datetime

def generate_power_load_data(start_year=2024, end_year=2024, random_seed=None):
    if random_seed is not None:
        np.random.seed(random_seed)
    
    all_data = []
    
    for year in range(start_year, end_year + 1):
        start_date = f'{year}-01-01'
        end_date = f'{year}-12-31'
        date_range = pd.date_range(start=start_date, end=end_date, freq='H')
        
        n = len(date_range)
        data = {
            'timestamp': date_range,
            'load_mw': np.zeros(n),
            'temperature_c': np.zeros(n),
            'wind_mps': np.zeros(n),
            'is_holiday': np.zeros(n),
            'capacity_mw': np.zeros(n)
        }
        
        holidays = [
            f'{year}-01-01', f'{year}-01-07', f'{year}-03-08', 
            f'{year}-05-01', f'{year}-05-09', f'{year}-06-28',
            f'{year}-08-24', f'{year}-10-14', f'{year}-12-25'
        ]
        holiday_dates = pd.to_datetime(holidays)
        
        for i, timestamp in enumerate(date_range):
            hour = timestamp.hour
            day_of_week = timestamp.weekday()
            day_of_year = timestamp.timetuple().tm_yday
            
            base_temp = 10 + 25 * np.sin(2 * np.pi * (day_of_year - 15) / 365)
            daily_temp_variation = 8 * np.sin(2 * np.pi * (hour - 6) / 24)
            temp_noise = np.random.normal(0, 2)
            data['temperature_c'][i] = base_temp + daily_temp_variation + temp_noise
            
            base_load = 4000 + 800 * np.sin(2 * np.pi * hour / 24)
            
            temp_effect = 0
            if data['temperature_c'][i] < 0:
                temp_effect = 300 * (0 - data['temperature_c'][i]) / 15
            elif data['temperature_c'][i] > 25:
                temp_effect = 200 * (data['temperature_c'][i] - 25) / 10
            
            seasonal_factor = 1 + 0.15 * np.sin(2 * np.pi * (day_of_year - 15) / 365)
            weekday_factor = 0.85 if day_of_week >= 5 else 1.0
            random_noise = np.random.normal(0, 120)
            
            data['load_mw'][i] = (base_load + temp_effect) * seasonal_factor * weekday_factor + random_noise
            data['wind_mps'][i] = np.random.gamma(2, 1.5)
            
            is_holiday = 1 if timestamp.normalize() in holiday_dates else 0
            data['is_holiday'][i] = is_holiday
            
            power_base = data['load_mw'][i] + 800
            power_noise = np.random.normal(0, 80)
            data['capacity_mw'][i] = power_base + power_noise
        
        df_year = pd.DataFrame(data)
        
        n = len(df_year)
        for i in range(n):
            hour = df_year.loc[i, 'timestamp'].hour
            if 7 <= hour <= 10 or 17 <= hour <= 20:
                df_year.loc[i, 'load_mw'] *= 1.12
        
        df_year['load_mw'] = np.clip(df_year['load_mw'], 2500, 5500)
        df_year['temperature_c'] = np.clip(df_year['temperature_c'], -15, 35)
        df_year['wind_mps'] = np.clip(df_year['wind_mps'], 0, 15)
        df_year['capacity_mw'] = np.clip(df_year['capacity_mw'], 5000, 7000)
        
        for col in ['load_mw', 'temperature_c', 'wind_mps', 'capacity_mw']:
            df_year[col] = df_year[col].round(1)
        
        df_year['year'] = year
        all_data.append(df_year)
    
    df = pd.concat(all_data, ignore_index=True)
    return df

def prepare_data(df):
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df['date'] = df['timestamp'].dt.date
    df['month'] = df['timestamp'].dt.month
    
    month_names_ua = {
        1: 'Січень', 2: 'Лютий', 3: 'Березень', 4: 'Квітень',
        5: 'Травень', 6: 'Червень', 7: 'Липень', 8: 'Серпень',
        9: 'Вересень', 10: 'Жовтень', 11: 'Листопад', 12: 'Грудень'
    }
    df['month_name'] = df['month'].map(month_names_ua)
    
    month_order = {
        'Січень': 1, 'Лютий': 2, 'Березень': 3, 'Квітень': 4,
        'Травень': 5, 'Червень': 6, 'Липень': 7, 'Серпень': 8,
        'Вересень': 9, 'Жовтень': 10, 'Листопад': 11, 'Грудень': 12
    }
    df['month_order'] = df['month_name'].map(month_order)
    
    df['quarter'] = df['timestamp'].dt.quarter
    df['hour'] = df['timestamp'].dt.hour
    df['day_type'] = df['is_holiday'].apply(lambda x: 'Свято' if x == 1 else 'Робочий')
    
    day_names_ua = {
        'Monday': 'Понеділок',
        'Tuesday': 'Вівторок',
        'Wednesday': 'Середа',
        'Thursday': 'Четвер',
        'Friday': 'П\'ятниця',
        'Saturday': 'Субота',
        'Sunday': 'Неділя'
    }
    df['day_of_week'] = df['timestamp'].dt.day_name().map(day_names_ua)
    
    return df

def create_csv_reports(df, output_dir, random_mode):
    output_path = os.path.abspath(output_dir)
    
    main_file = os.path.join(output_path, "power_load_data.csv")
    df.to_csv(main_file, index=False, encoding='utf-8')
    
    daily_pivot = pd.pivot_table(
        df,
        values='load_mw',
        index=[df['timestamp'].dt.date, 'month_name'],
        columns='day_type',
        aggfunc='mean'
    ).round(1)
    daily_pivot.to_csv(os.path.join(output_path, "daily_load_analysis.csv"))
    
    monthly_pivot = pd.pivot_table(
        df,
        values='load_mw',
        index='month_name',
        columns='year',
        aggfunc='mean'
    ).round(1)
    monthly_pivot.to_csv(os.path.join(output_path, "monthly_load_analysis.csv"))
    
    create_text_report(df, output_path, random_mode)

def create_text_report(df, output_path, random_mode):
    report_file = os.path.join(output_path, "power_load_analysis_report.txt")
    
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write("ЗВІТ З АНАЛІЗУ НАВАНТАЖЕННЯ ЕНЕРГОСИСТЕМИ\n")
        f.write("=" * 50 + "\n\n")
        f.write(f"Дата генерації: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
        f.write(f"Період аналізу: {df['year'].min()} - {df['year'].max()} роки\n")
        f.write(f"Режим генерації: {random_mode}\n\n")
        
        f.write("СТАТИСТИКА ДАНИХ:\n")
        f.write(f"- Загальна кількість записів: {len(df):,}\n")
        f.write(f"- Середнє навантаження: {df['load_mw'].mean():.1f} МВт\n")
        f.write(f"- Максимальне навантаження: {df['load_mw'].max():.1f} МВт\n")
        f.write(f"- Мінімальне навантаження: {df['load_mw'].min():.1f} МВт\n")
        f.write(f"- Середня температура: {df['temperature_c'].mean():.1f} °C\n\n")
        
        f.write("ДОСТУПНІ ЗВЕДЕНІ ТАБЛИЦІ:\n")
        f.write("1. Погодинний моніторинг - за конкретний день\n")
        f.write("2. Місячний моніторинг - за рік\n")
        f.write("3. Споживання за день\n")
        f.write("4. Споживання за місяць\n")

def get_random_mode_description(mode):
    if mode == "reproducible":
        return "Відтворювані дані - однакові результати при кожному запуску"
    else:
        return "Випадкові дані - унікальні результати при кожному запуску"
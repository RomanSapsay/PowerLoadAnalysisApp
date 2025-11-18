import matplotlib.pyplot as plt
import numpy as np

def plot_hourly(ax, day_data, selected_date):
    ax.clear()
    
    hours = day_data['hour']
    load = day_data['load_mw']
    
    color = 'tab:blue'
    ax.set_xlabel('Година')
    ax.set_ylabel('Навантаження (МВт)', color=color)
    ax.plot(hours, load, color=color, linewidth=2, label='Навантаження')
    ax.tick_params(axis='y', labelcolor=color)
    ax.grid(True, alpha=0.3)
    
    ax.set_title(f'Погодинне навантаження - {selected_date}')
    ax.set_xlim(0, 23)
    ax.set_xticks(range(0, 24, 2))
    
    ax.legend(loc='upper left')

def plot_monthly_monitor(ax, monthly_stats, year):
    ax.clear()
    
    months = [row[1] for row in monthly_stats.index]
    max_loads = monthly_stats['max_load']
    min_loads = monthly_stats['min_load']
    avg_loads = monthly_stats['avg_load']
    
    x_pos = range(len(months))
    ax.plot(x_pos, max_loads, color='red', linewidth=2, marker='o', label='Макс. навантаження')
    ax.plot(x_pos, min_loads, color='blue', linewidth=2, marker='o', label='Мін. навантаження')
    ax.plot(x_pos, avg_loads, color='green', linewidth=2, marker='o', label='Середнє навантаження')
    
    ax.fill_between(x_pos, min_loads, max_loads, 
                   alpha=0.2, color='gray', label='Діапазон навантаження')
    
    ax.set_xlabel('Місяць')
    ax.set_ylabel('Навантаження (МВт)')
    ax.set_title(f'Місячний моніторинг навантаження - {year} рік')
    ax.grid(True, alpha=0.3)
    ax.legend(loc='upper right')
    
    ax.set_xticks(x_pos)
    ax.set_xticklabels(months, rotation=45)

def plot_daily_consumption(ax, daily_stats, year, month_name):
    ax.clear()
    
    dates = [str(date) for date, _ in daily_stats.index]
    total_energy = daily_stats['total_energy']
    
    ax.plot(dates, total_energy, color='purple', linewidth=2, marker='o', markersize=4, label='Спожита енергія')
    
    ax.set_xlabel('Дата')
    ax.set_ylabel('Спожита енергія (МВт·год)')
    ax.set_title(f'Добове споживання енергії - {month_name} {year} рік')
    ax.grid(True, alpha=0.3)
    ax.legend()
    
    if len(total_energy) > 0:
        min_energy = total_energy.min()
        max_energy = total_energy.max()
        padding = (max_energy - min_energy) * 0.1
        ax.set_ylim(min_energy - padding, max_energy + padding)
    
    ax.tick_params(axis='x', rotation=45)
    
    n = len(dates)
    if n > 0:
        step = max(1, n // 10)
        ax.set_xticks(range(0, n, step))
        ax.set_xticklabels([dates[i] for i in range(0, n, step)], rotation=45)

def plot_daily_load(ax, daily_stats, year, month_name):
    ax.clear()
    
    dates = [str(date) for date, _ in daily_stats.index]
    avg_load = daily_stats['avg_load']
    max_load = daily_stats['max_load']
    
    ax.plot(dates, avg_load, color='green', linewidth=2, marker='o', markersize=4, label='Середнє навантаження')
    ax.plot(dates, max_load, color='red', linewidth=2, marker='s', markersize=4, label='Максимальне навантаження')
    
    ax.set_xlabel('Дата')
    ax.set_ylabel('Навантаження (МВт)')
    ax.set_title(f'Добове навантаження - {month_name} {year} рік')
    ax.grid(True, alpha=0.3)
    ax.legend()
    
    ax.tick_params(axis='x', rotation=45)
    
    n = len(dates)
    if n > 0:
        step = max(1, n // 10)
        ax.set_xticks(range(0, n, step))
        ax.set_xticklabels([dates[i] for i in range(0, n, step)], rotation=45)

def plot_monthly_consumption(ax, monthly_consumption):
    ax.clear()
    
    years = sorted(monthly_consumption.index.get_level_values('year').unique())
    
    months_ukrainian = ['Січень', 'Лютий', 'Березень', 'Квітень', 'Травень', 'Червень',
                       'Липень', 'Серпень', 'Вересень', 'Жовтень', 'Листопад', 'Грудень']
    
    x_pos = np.arange(len(months_ukrainian))
    
    for i, year in enumerate(years):
        year_data = monthly_consumption.xs(year, level='year')
        
        monthly_energy = []
        for month_idx in range(1, 13):
            month_data = year_data[year_data.index.get_level_values('month') == month_idx]
            if not month_data.empty:
                monthly_energy.append(month_data['total_energy'].iloc[0])
            else:
                monthly_energy.append(0)
        
        ax.plot(x_pos, monthly_energy, color=f'C{i}', linewidth=2, marker='o', 
                label=f'{year} - Спожита енергія')
    
    ax.set_xlabel('Місяць')
    ax.set_ylabel('Спожита енергія (МВт·год)')
    ax.set_title('Місячне споживання енергії')
    ax.legend(title='Рік')
    ax.grid(True, alpha=0.3)
    
    ax.set_xticks(x_pos)
    ax.set_xticklabels(months_ukrainian, rotation=45)

def plot_monthly_load(ax, monthly_consumption):
    ax.clear()
    
    years = sorted(monthly_consumption.index.get_level_values('year').unique())
    
    months_ukrainian = ['Січень', 'Лютий', 'Березень', 'Квітень', 'Травень', 'Червень',
                       'Липень', 'Серпень', 'Вересень', 'Жовтень', 'Листопад', 'Грудень']
    
    x_pos = np.arange(len(months_ukrainian))
    
    for i, year in enumerate(years):
        year_data = monthly_consumption.xs(year, level='year')
        
        monthly_avg_load = []
        monthly_max_load = []
        
        for month_idx in range(1, 13):
            month_data = year_data[year_data.index.get_level_values('month') == month_idx]
            if not month_data.empty:
                monthly_avg_load.append(month_data['avg_load'].iloc[0])
                monthly_max_load.append(month_data['max_load'].iloc[0])
            else:
                monthly_avg_load.append(0)
                monthly_max_load.append(0)
        
        ax.plot(x_pos, monthly_avg_load, color=f'C{i}', linewidth=2, marker='o', 
                label=f'{year} - Середнє навантаження')
        ax.plot(x_pos, monthly_max_load, color=f'C{i}', linewidth=2, marker='s', 
                linestyle='--', label=f'{year} - Макс. навантаження')
    
    ax.set_xlabel('Місяць')
    ax.set_ylabel('Навантаження (МВт)')
    ax.set_title('Місячне навантаження')
    ax.legend(title='Показники за роками', loc='upper left', bbox_to_anchor=(1, 1))
    ax.grid(True, alpha=0.3)
    
    ax.set_xticks(x_pos)
    ax.set_xticklabels(months_ukrainian, rotation=45)
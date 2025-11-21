import matplotlib.pyplot as plt
import numpy as np

# --- ТЕМНА ТЕМА ---
THEME = {
    'bg': '#2d2d2d',
    'fg': '#ffffff',
    'grid': '#444444',
    'line_primary': '#00e5ff',   # Cyan
    'line_secondary': '#00e676', # Green
    'line_tertiary': '#ff2a68',  # Red/Pink
    'scatter': '#ffea00',        # Yellow
    'fill': '#00e5ff'
}

def setup_chart_style(ax, title, xlabel, ylabel):
    """Універсальний стилізатор"""
    fig = ax.figure
    fig.patch.set_facecolor(THEME['bg'])
    ax.set_facecolor(THEME['bg'])
    
    ax.set_title(title, color=THEME['fg'], pad=10, fontsize=9, fontweight='bold')
    ax.set_xlabel(xlabel, color=THEME['fg'], fontsize=8)
    ax.set_ylabel(ylabel, color=THEME['fg'], fontsize=8)
    
    ax.tick_params(axis='x', colors=THEME['fg'], labelsize=8)
    ax.tick_params(axis='y', colors=THEME['fg'], labelsize=8)
    
    ax.grid(True, color=THEME['grid'], linestyle='--', alpha=0.5)
    
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['bottom'].set_color(THEME['grid'])
    ax.spines['left'].set_color(THEME['grid'])

def plot_hourly_dashboard(fig, day_data, selected_date):
    """Малює ДВА графіки: Часовий ряд та Кореляцію"""
    ax1 = fig.add_subplot(211) # Верхній графік
    ax2 = fig.add_subplot(212) # Нижній графік
    
    # --- Графік 1: Профіль навантаження ---
    hours = day_data['hour']
    load = day_data['load_mw']
    
    ax1.plot(hours, load, color=THEME['line_primary'], linewidth=2, label='Навантаження')
    ax1.fill_between(hours, load, alpha=0.15, color=THEME['fill'])
    
    setup_chart_style(ax1, f'Профіль: {selected_date}', 'Година', 'МВт')
    ax1.set_xlim(0, 23)
    ax1.set_xticks(range(0, 24, 2))
    
    # --- Графік 2: Кореляція (Температура vs Навантаження) ---
    temp = day_data['temperature_c']
    
    # Малюємо точки
    scatter = ax2.scatter(temp, load, color=THEME['scatter'], alpha=0.7, s=40, edgecolors='black', linewidth=0.5)
    
    # Лінія тренду (поліноміальна регресія для краси)
    try:
        z = np.polyfit(temp, load, 2) # Квадратична залежність
        p = np.poly1d(z)
        xp = np.linspace(temp.min(), temp.max(), 100)
        ax2.plot(xp, p(xp), color=THEME['line_tertiary'], linestyle='--', alpha=0.8, label='Тренд')
    except: pass

    setup_chart_style(ax2, 'Аналіз залежності: Температура vs Навантаження', 'Температура (°C)', 'Навантаження (МВт)')
    ax2.legend(facecolor=THEME['bg'], edgecolor=THEME['grid'], labelcolor=THEME['fg'], fontsize=8)

    fig.tight_layout(pad=2.0)

def plot_monthly_dashboard(fig, monthly_stats, year):
    """Малює ДВА графіки: Динаміку та BoxPlot (Розподіл)"""
    ax1 = fig.add_subplot(211)
    ax2 = fig.add_subplot(212)
    
    months = [row[1] for row in monthly_stats.index]
    x = np.arange(len(months))
    
    # --- Графік 1: Мін/Макс/Середнє ---
    ax1.plot(x, monthly_stats['max_load'], color=THEME['line_tertiary'], marker='.', label='Макс')
    ax1.plot(x, monthly_stats['avg_load'], color=THEME['line_secondary'], marker='.', label='Серед')
    ax1.plot(x, monthly_stats['min_load'], color=THEME['line_primary'], marker='.', label='Мін')
    
    ax1.fill_between(x, monthly_stats['min_load'], monthly_stats['max_load'], alpha=0.1, color='gray')
    
    setup_chart_style(ax1, f'Моніторинг ({year})', 'Місяць', 'МВт')
    ax1.set_xticks(x)
    ax1.set_xticklabels(months, rotation=0, fontsize=8)
    ax1.legend(facecolor=THEME['bg'], edgecolor=THEME['grid'], labelcolor=THEME['fg'], loc='upper right', fontsize=8)
    
    # --- Графік 2: Гістограма розподілу (Волатильність) ---
    # Ми імітуємо BoxPlot використовуючи статистику, яку маємо (мін, макс, середнє)
    # Для справжнього BoxPlot треба сирі дані, але ми зробимо візуалізацію "Діапазону" (Error Bar Style)
    
    ax2.bar(x, monthly_stats['max_load'] - monthly_stats['min_load'], bottom=monthly_stats['min_load'], 
            color=THEME['fill'], alpha=0.3, edgecolor=THEME['line_primary'], label='Діапазон коливань')
    
    # Лінія середнього поверх стовпчиків
    ax2.plot(x, monthly_stats['avg_load'], color='white', marker='_', markersize=20, linestyle='None', label='Середнє')
    
    setup_chart_style(ax2, 'Волатильність (Стабільність навантаження)', 'Місяць', 'Діапазон (МВт)')
    ax2.set_xticks(x)
    ax2.set_xticklabels(months, rotation=0, fontsize=8)
    
    fig.tight_layout(pad=2.0)

def plot_daily_consumption(ax, daily_stats, year, month_name):
    ax.clear()
    dates = [str(date)[-2:] for date, _ in daily_stats.index]
    ax.bar(dates, daily_stats['total_energy'], color=THEME['line_primary'], alpha=0.7)
    setup_chart_style(ax, f'Споживання: {month_name} {year}', 'День', 'МВт·год')
    
    n = len(dates)
    if n > 0:
        step = max(1, n // 15)
        ax.set_xticks(range(0, n, step))
        ax.set_xticklabels([dates[i] for i in range(0, n, step)])

def plot_monthly_consumption(ax, stats):
    ax.clear()
    years = stats.index.get_level_values('year').unique()
    months_ukr = ['Січ', 'Лют', 'Бер', 'Кві', 'Тра', 'Чер', 'Лип', 'Сер', 'Вер', 'Жов', 'Лис', 'Гру']
    x = np.arange(len(months_ukr))
    
    for i, year in enumerate(years):
        try:
            year_data = stats.xs(year, level='year')
            values = []
            for m_idx in range(1, 13):
                val = 0
                rows = year_data[year_data.index.get_level_values('month') == m_idx]
                if not rows.empty: val = rows['total_energy'].iloc[0]
                values.append(val)
            ax.plot(x, values, marker='o', linewidth=2, label=str(year))
        except: pass

    setup_chart_style(ax, 'Річна динаміка', 'Місяць', 'МВт·год')
    ax.set_xticks(x)
    ax.set_xticklabels(months_ukr)
    ax.legend(facecolor=THEME['bg'], edgecolor=THEME['grid'], labelcolor=THEME['fg'])

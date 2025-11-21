import tkinter as tk
from tkinter import ttk
import pandas as pd
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure
import plotting

class BaseAnalysisTab(ttk.Frame):
    """
    Базовий клас для вкладок аналізу.
    Включає: Верхній тулбар, Графік з навігацією (Zoom), Таблицю даних.
    """
    def __init__(self, parent, app_context):
        super().__init__(parent)
        self.app = app_context
        self.setup_layout()

    def setup_layout(self):
        self.configure(style='TFrame')
        
        # --- 1. ВЕРХНЯ ПАНЕЛЬ (TOOLBAR) ---
        self.top_bar = ttk.Frame(self, style='Card.TFrame', padding=(10, 5))
        self.top_bar.pack(side=tk.TOP, fill='x', padx=10, pady=(10, 0))
        
        # Зона контролів (зліва)
        self.controls_area = ttk.Frame(self.top_bar, style='Card.TFrame')
        self.controls_area.pack(side=tk.LEFT)
        ttk.Label(self.controls_area, text="Налаштування:", style='Card.TLabel', font=('Segoe UI', 9, 'bold')).pack(side=tk.LEFT, padx=(0, 10))
        
        self.add_controls()
        
        # Кнопка оновлення (справа)
        ttk.Button(self.top_bar, text="↺ Оновити", command=self.update_data).pack(side=tk.RIGHT)

        # --- 2. ОСНОВНИЙ КОНТЕНТ ---
        content = ttk.Frame(self, style='TFrame')
        content.pack(fill='both', expand=True, padx=10, pady=10)
        
        # --- ЛІВА ЧАСТИНА: ГРАФІК ---
        graph_container = ttk.Frame(content, style='TFrame')
        graph_container.pack(side=tk.LEFT, fill='both', expand=True, padx=(0, 5))

        # Створюємо фігуру з темним фоном
        self.fig = Figure(figsize=(6, 6), dpi=100, facecolor='#2d2d2d')
        
        self.canvas = FigureCanvasTkAgg(self.fig, graph_container)
        self.canvas.get_tk_widget().pack(fill='both', expand=True)

        # Панель навігації (Zoom, Pan, Save)
        toolbar_frame = ttk.Frame(graph_container)
        toolbar_frame.pack(fill='x')
        
        self.mpl_toolbar = NavigationToolbar2Tk(self.canvas, toolbar_frame)
        self.mpl_toolbar.update()
        
        # Стилізація навігаційної панелі під темну тему
        self.mpl_toolbar.config(background='#2d2d2d')
        for button in self.mpl_toolbar.winfo_children():
            try: button.config(background='#2d2d2d')
            except: pass

        # --- ПРАВА ЧАСТИНА: ТАБЛИЦЯ ---
        table_container = ttk.Frame(content, style='TFrame')
        table_container.pack(side=tk.RIGHT, fill='y', padx=(5, 0))
        table_container.configure(width=380) # Трохи ширше для читабельності

        ttk.Label(table_container, text="Детальні дані", style='TLabel', font=('Segoe UI', 10, 'bold')).pack(anchor='w', pady=(0, 5))
        
        cols = self.get_columns()
        self.tree = ttk.Treeview(table_container, columns=cols, show="headings")
        
        for col in cols:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=85, anchor='center')
        
        scroll = ttk.Scrollbar(table_container, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        
        self.tree.pack(side=tk.LEFT, fill='both', expand=True)
        scroll.pack(side=tk.RIGHT, fill='y')

    def add_controls(self): pass
    def get_columns(self): return []
    def update_data(self): pass
    def clear_tree(self):
        for item in self.tree.get_children(): self.tree.delete(item)

# --- РЕАЛІЗАЦІЯ ВКЛАДОК ---

class HourlyTab(BaseAnalysisTab):
    def get_columns(self): return ("Година", "МВт", "Temp", "Cap")
    
    def add_controls(self):
        ttk.Label(self.controls_area, text="День:", style='Card.TLabel').pack(side=tk.LEFT)
        self.date_combo = ttk.Combobox(self.controls_area, state="readonly", width=12)
        self.date_combo.pack(side=tk.LEFT, padx=5)
        
    def update_controls_state(self):
        if self.app.df is not None:
            dates = sorted(self.app.df['date'].unique().astype(str))
            self.date_combo['values'] = dates
            if dates: self.date_combo.set(dates[0])
            
    def update_data(self):
        if self.app.df is None: return
        try:
            sel_date = pd.to_datetime(self.date_combo.get()).date()
            data = self.app.df[self.app.df['date'] == sel_date]
            
            self.clear_tree()
            for _, r in data.iterrows():
                self.tree.insert("", "end", values=(
                    f"{r['hour']:02d}", 
                    f"{r['load_mw']:.0f}", 
                    f"{r['temperature_c']:.1f}", 
                    f"{r['capacity_mw']:.0f}"
                ))
            
            self.fig.clear()
            plotting.plot_hourly_dashboard(self.fig, data, sel_date)
            self.canvas.draw()
        except Exception: pass

class MonthlyMonitorTab(BaseAnalysisTab):
    def get_columns(self): return ("Міс", "Макс", "Мін", "Сер")
    
    def add_controls(self):
        ttk.Label(self.controls_area, text="Рік:", style='Card.TLabel').pack(side=tk.LEFT)
        self.year_combo = ttk.Combobox(self.controls_area, state="readonly", width=8)
        self.year_combo.pack(side=tk.LEFT, padx=5)
        
    def update_controls_state(self):
        if self.app.df is not None:
            years = sorted(self.app.df['year'].unique().astype(str))
            self.year_combo['values'] = years
            if years: self.year_combo.set(years[0])
            
    def update_data(self):
        if self.app.df is None: return
        try:
            year = int(self.year_combo.get())
            data = self.app.df[self.app.df['year'] == year]
            stats = data.groupby(['month', 'month_name']).agg({
                'load_mw': ['max', 'min', 'mean', 'sum']
            }).round(1)
            stats.columns = ['max_load', 'min_load', 'avg_load', 'total_consumption']
            stats = stats.sort_index(level='month')
            
            self.clear_tree()
            for (idx, name), r in stats.iterrows():
                self.tree.insert("", "end", values=(
                    name, 
                    f"{r['max_load']:.1f}", 
                    f"{r['min_load']:.1f}", 
                    f"{r['avg_load']:.1f}"
                ))
            
            self.fig.clear()
            plotting.plot_monthly_dashboard(self.fig, stats, year)
            self.canvas.draw()
        except Exception: pass

class DailyConsumptionTab(BaseAnalysisTab):
    def get_columns(self): return ("Дата", "Спож.", "Сер.", "Макс")
    
    def add_controls(self):
        ttk.Label(self.controls_area, text="Рік:", style='Card.TLabel').pack(side=tk.LEFT)
        self.year_combo = ttk.Combobox(self.controls_area, state="readonly", width=8)
        self.year_combo.pack(side=tk.LEFT, padx=5)
        
        ttk.Label(self.controls_area, text="Міс:", style='Card.TLabel').pack(side=tk.LEFT)
        self.month_combo = ttk.Combobox(self.controls_area, state="readonly", width=5, 
                                      values=[str(i) for i in range(1,13)])
        self.month_combo.pack(side=tk.LEFT, padx=5)
        self.month_combo.set('1')
        
    def update_controls_state(self):
        if self.app.df is not None:
            years = sorted(self.app.df['year'].unique().astype(str))
            self.year_combo['values'] = years
            if years: self.year_combo.set(years[0])
            
    def update_data(self):
        if self.app.df is None: return
        try:
            y, m = int(self.year_combo.get()), int(self.month_combo.get())
            data = self.app.df[(self.app.df['year'] == y) & (self.app.df['month'] == m)]
            
            stats = data.groupby(['date', 'day_type']).agg({'load_mw': ['sum', 'mean', 'max']}).round(1)
            stats.columns = ['total_energy', 'avg_load', 'max_load']
            
            self.clear_tree()
            for (d, t), r in stats.iterrows():
                self.tree.insert("", "end", values=(
                    str(d), 
                    f"{r['total_energy']:.0f}", 
                    f"{r['avg_load']:.1f}", 
                    f"{r['max_load']:.1f}"
                ))
            
            self.fig.clear()
            ax = self.fig.add_subplot(111)
            month_name = data['month_name'].iloc[0] if not data.empty else ""
            plotting.plot_daily_consumption(ax, stats, y, month_name)
            self.canvas.draw()
        except Exception: pass

class MonthlyConsumptionTab(BaseAnalysisTab):
    def get_columns(self): return ("Рік", "Міс", "Спож.", "Сер.", "Макс")
    
    def add_controls(self):
        ttk.Label(self.controls_area, text="За весь період (Порівняння років)", 
                 style='Card.TLabel').pack(side=tk.LEFT)
                 
    def update_data(self):
        if self.app.df is None: return
        try:
            stats = self.app.df.groupby(['year', 'month_name', 'month']).agg({
                'load_mw': ['sum', 'mean', 'max'], 'date': 'nunique'
            }).round(1)
            stats.columns = ['total_energy', 'avg_load', 'max_load', 'days_count']
            stats = stats.sort_index(level=['year', 'month'])
            
            self.clear_tree()
            for (y, name, m), r in stats.iterrows():
                # ВИПРАВЛЕНО ОКРУГЛЕННЯ ТУТ:
                self.tree.insert("", "end", values=(
                    y, 
                    name, 
                    f"{r['total_energy']:.0f}", 
                    f"{r['avg_load']:.1f}", 
                    f"{r['max_load']:.1f}"
                ))
            
            self.fig.clear()
            ax = self.fig.add_subplot(111)
            plotting.plot_monthly_consumption(ax, stats)
            self.canvas.draw()
        except Exception: pass

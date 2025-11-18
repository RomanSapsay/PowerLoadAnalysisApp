import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import os
import platform
import subprocess
import pandas as pd
import matplotlib
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import logic
import plotting

matplotlib.rcParams['font.family'] = 'DejaVu Sans'
matplotlib.rcParams['font.sans-serif'] = ['DejaVu Sans']
matplotlib.rcParams['axes.unicode_minus'] = False

class PowerLoadAnalysisApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Аналіз навантаження енергосистеми")
        self.root.geometry("1200x700")
        self.root.configure(bg='#f0f0f0')
        
        self.start_year = tk.StringVar(value="2024")
        self.end_year = tk.StringVar(value="2024")
        self.random_mode = tk.StringVar(value="reproducible")
        default_dir = os.path.join(os.getcwd(), "results", "power_load_analysis")
        self.output_dir = tk.StringVar(value=default_dir)
        self.progress = tk.DoubleVar()
        self.status_text = tk.StringVar(value="Готовий до роботи")
        self.result_text = tk.StringVar(value="")
        
        self.selected_date = tk.StringVar(value="2024-01-01")
        self.selected_year_filter = tk.StringVar(value="2024")
        
        self.selected_year_monthly = tk.StringVar(value="2024")
        
        self.selected_year_daily = tk.StringVar(value="2024")
        self.selected_month_daily = tk.StringVar(value="1")
        
        self.df = None
        self.setup_ui()
    
    def open_results_dir(self):
        directory = self.output_dir.get()
        abs_directory = os.path.abspath(directory)
        
        if os.path.exists(abs_directory):
            try:
                if platform.system() == "Windows":
                    os.startfile(abs_directory)
                elif platform.system() == "Darwin":
                    subprocess.call(["open", abs_directory])
                else:
                    subprocess.call(["xdg-open", abs_directory])
            except Exception as e:
                messagebox.showerror("Помилка", f"Не вдалося відкрити папку: {str(e)}")
        else:
            messagebox.showwarning("Увага", f"Папка результатів ще не створена!\nШлях: {abs_directory}")

    def get_random_seed(self):
        if self.random_mode.get() == "reproducible":
            return 42
        else:
            return None

    def run_analysis(self, start_year, end_year):
        try:
            random_seed = self.get_random_seed()
            self.update_progress(0, "Початок генерації даних...")
            
            output_path = os.path.abspath(self.output_dir.get())
            os.makedirs(output_path, exist_ok=True)
            
            self.update_progress(30, "Генерація даних...")
            self.df = logic.generate_power_load_data(start_year, end_year, random_seed)
            
            self.update_progress(60, "Підготовка даних для аналізу...")
            self.df = logic.prepare_data(self.df)
            
            self.update_progress(80, "Створення звітів...")
            logic.create_csv_reports(self.df, self.output_dir.get(), self.get_random_mode_description())
            
            self.update_progress(90, "Налаштування інтерфейсу...")
            self.setup_pivot_tabs()
            self.update_all_pivot_tables()
            
            self.update_progress(100, "Завершено!")
            self.result_text.set(f"CSV файли збережено в:\n{output_path}")
            messagebox.showinfo("Завершено", "Генерація успішно завершена!")
            
        except Exception as e:
            self.result_text.set("")
            messagebox.showerror("Помилка", f"Сталася помилка під час виконання:\n{str(e)}")
        finally:
            self.generate_btn.config(state='normal')

    def select_output_dir(self):
        current_dir = self.output_dir.get()
        if not os.path.isabs(current_dir):
            current_dir = os.path.abspath(current_dir)
        
        directory = filedialog.askdirectory(initialdir=current_dir)
        if directory:
            self.output_dir.set(directory)
    
    def update_progress(self, value, message):
        self.progress.set(value)
        self.status_text.set(message)
        self.root.update_idletasks()
    
    def start_analysis(self):
        try:
            start_year = int(self.start_year.get())
            end_year = int(self.end_year.get())
            
            if start_year > end_year:
                messagebox.showerror("Помилка", "Початковий рік не може бути більшим за кінцевий!")
                return
            
            self.result_text.set("")
            self.generate_btn.config(state='disabled')
            
            thread = threading.Thread(target=self.run_analysis, args=(start_year, end_year))
            thread.daemon = True
            thread.start()
            
        except ValueError as e:
            messagebox.showerror("Помилка", "Будь ласка, введіть коректні числові значення!")

    def get_random_mode_description(self):
        return logic.get_random_mode_description(self.random_mode.get())

    def setup_ui(self):
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=10)
        
        self.setup_generation_tab()
        self.pivot_tabs = {}
    
    def setup_generation_tab(self):
        gen_frame = ttk.Frame(self.notebook)
        self.notebook.add(gen_frame, text="Генерація даних")
        
        title_label = ttk.Label(gen_frame, text="Аналіз навантаження енергосистеми", 
                               font=('Arial', 16, 'bold'))
        title_label.pack(pady=(0, 20))
        
        params_frame = ttk.LabelFrame(gen_frame, text="Параметри генерації даних", padding="10")
        params_frame.pack(fill='x', padx=10, pady=(0, 10))
        
        params_row1 = ttk.Frame(params_frame)
        params_row1.pack(fill='x', pady=5)
        ttk.Label(params_row1, text="Початковий рік:").pack(side=tk.LEFT, padx=(0, 10))
        start_year_entry = ttk.Entry(params_row1, textvariable=self.start_year, width=10)
        start_year_entry.pack(side=tk.LEFT, padx=(0, 20))
        
        ttk.Label(params_row1, text="Кінцевий рік:").pack(side=tk.LEFT, padx=(0, 10))
        end_year_entry = ttk.Entry(params_row1, textvariable=self.end_year, width=10)
        end_year_entry.pack(side=tk.LEFT, padx=(0, 20))
        
        ttk.Label(params_row1, text="Режим даних:").pack(side=tk.LEFT, padx=(0, 10))
        
        mode_frame = ttk.Frame(params_row1)
        mode_frame.pack(side=tk.LEFT, padx=(0, 10))
        
        self.reproducible_btn = ttk.Button(
            mode_frame, 
            text="Відтворювані", 
            command=lambda: self.set_random_mode("reproducible"),
            width=15
        )
        self.reproducible_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        self.random_btn = ttk.Button(
            mode_frame, 
            text="Випадкові", 
            command=lambda: self.set_random_mode("random"),
            width=15
        )
        self.random_btn.pack(side=tk.LEFT)
        
        self.update_mode_buttons()
        
        params_row2 = ttk.Frame(params_frame)
        params_row2.pack(fill='x', pady=5)
        ttk.Label(params_row2, text="Папка результатів:").pack(side=tk.LEFT, padx=(0, 10))
        ttk.Entry(params_row2, textvariable=self.output_dir, width=50).pack(side=tk.LEFT, fill='x', expand=True, padx=(0, 10))
        ttk.Button(params_row2, text="Обрати...", command=self.select_output_dir).pack(side=tk.LEFT)
        
        desc_frame = ttk.Frame(params_frame)
        desc_frame.pack(fill='x', pady=5)
        self.mode_description = ttk.Label(
            desc_frame, 
            text=self.get_random_mode_description(),
            foreground='blue',
            font=('Arial', 9)
        )
        self.mode_description.pack(side=tk.LEFT)
        
        buttons_frame = ttk.Frame(gen_frame)
        buttons_frame.pack(fill='x', padx=10, pady=10)
        
        self.generate_btn = ttk.Button(buttons_frame, text="Згенерувати дані", command=self.start_analysis)
        self.generate_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(buttons_frame, text="Відкрити папку результатів", command=self.open_results_dir).pack(side=tk.LEFT, padx=(0, 10))
        
        progress_frame = ttk.LabelFrame(gen_frame, text="Прогрес виконання", padding="10")
        progress_frame.pack(fill='x', padx=10, pady=(0, 10))
        
        self.progress_bar = ttk.Progressbar(progress_frame, variable=self.progress, maximum=100)
        self.progress_bar.pack(fill='x')
        
        ttk.Label(progress_frame, textvariable=self.status_text).pack(pady=(5, 0))
        
        result_frame = ttk.Frame(gen_frame)
        result_frame.pack(fill='x', padx=10, pady=(0, 10))
        
        self.result_label = ttk.Label(
            result_frame, 
            textvariable=self.result_text,
            foreground='green',
            font=('Arial', 9),
            wraplength=900
        )
        self.result_label.pack(fill='x')

    def set_random_mode(self, mode):
        self.random_mode.set(mode)
        self.update_mode_buttons()
        self.mode_description.config(text=self.get_random_mode_description())

    def update_mode_buttons(self):
        mode = self.random_mode.get()
        
        for btn in [self.reproducible_btn, self.random_btn]:
            btn.state(['!pressed'])
        
        if mode == "reproducible":
            self.reproducible_btn.state(['pressed'])
        else:
            self.random_btn.state(['pressed'])

    def setup_pivot_tabs(self):
        for tab_id in list(self.pivot_tabs.keys()):
            self.notebook.forget(self.pivot_tabs[tab_id])
        self.pivot_tabs.clear()
        
        tabs_config = [
            ("1_Погодинний моніторинг", self.setup_hourly_monitoring_tab),
            ("2_Місячний моніторинг", self.setup_monthly_monitoring_tab),
            ("3_Споживання за день", self.setup_daily_consumption_tab),
            ("4_Споживання за місяць", self.setup_monthly_consumption_tab)
        ]
        
        for tab_name, setup_func in tabs_config:
            tab_frame = ttk.Frame(self.notebook)
            self.notebook.add(tab_frame, text=tab_name.split('_')[1])
            self.pivot_tabs[tab_name] = tab_frame
            setup_func(tab_frame)
    
    def setup_hourly_monitoring_tab(self, parent):
        main_container = ttk.Frame(parent)
        main_container.pack(fill='both', expand=True, padx=10, pady=10)
        
        left_frame = ttk.Frame(main_container)
        left_frame.pack(side=tk.LEFT, fill='both', expand=True, padx=(0, 5))
        
        right_frame = ttk.Frame(main_container)
        right_frame.pack(side=tk.RIGHT, fill='both', expand=False, padx=(5, 0))
        right_frame.configure(width=400)
        
        control_frame = ttk.Frame(left_frame)
        control_frame.pack(fill='x', pady=(0, 10))
        
        ttk.Label(control_frame, text="Оберіть дату:").pack(side=tk.LEFT, padx=(0, 10))
        
        if self.df is not None:
            dates = sorted(self.df['date'].unique())
            date_combo = ttk.Combobox(control_frame, textvariable=self.selected_date, 
                                    values=[str(d) for d in dates], state="readonly")
            date_combo.pack(side=tk.LEFT, padx=(0, 10))
            date_combo.set(str(dates[0]) if dates else "")
        
        ttk.Button(control_frame, text="Оновити", command=self.update_hourly_monitoring).pack(side=tk.LEFT)
        
        graph_frame = ttk.LabelFrame(left_frame, text="Графік навантаження", padding="5")
        graph_frame.pack(fill='both', expand=True)
        
        self.hourly_fig = Figure(figsize=(8, 6), dpi=100)
        self.hourly_ax = self.hourly_fig.add_subplot(111)
        
        self.hourly_canvas = FigureCanvasTkAgg(self.hourly_fig, graph_frame)
        self.hourly_canvas.get_tk_widget().pack(fill='both', expand=True)
        
        table_frame = ttk.LabelFrame(right_frame, text="Погодинні дані", padding="5")
        table_frame.pack(fill='both', expand=True)
        
        columns = ("Година", "Навантаження (МВт)", "Температура (°C)", "Потужність (МВт)")
        self.hourly_tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=25)
        
        for col in columns:
            self.hourly_tree.heading(col, text=col)
            if col == "Година":
                self.hourly_tree.column(col, width=80)
            else:
                self.hourly_tree.column(col, width=100)
        
        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.hourly_tree.yview)
        self.hourly_tree.configure(yscrollcommand=scrollbar.set)
        
        self.hourly_tree.pack(side=tk.LEFT, fill='both', expand=True)
        scrollbar.pack(side=tk.RIGHT, fill='y')
    
    def update_hourly_monitoring(self):
        if self.df is None:
            return
        
        try:
            selected_date = pd.to_datetime(self.selected_date.get()).date()
            day_data = self.df[self.df['date'] == selected_date]
            
            for item in self.hourly_tree.get_children():
                self.hourly_tree.delete(item)
            
            for _, row in day_data.iterrows():
                self.hourly_tree.insert("", "end", values=(
                    f"{row['hour']:02d}:00",
                    f"{row['load_mw']:.1f}",
                    f"{row['temperature_c']:.1f}",
                    f"{row['capacity_mw']:.1f}"
                ))
            
            self.update_hourly_plot(day_data, selected_date)
            
        except Exception as e:
            messagebox.showerror("Помилка", f"Помилка при оновленні погодинного моніторингу: {str(e)}")
    
    def update_hourly_plot(self, day_data, selected_date):
        plotting.plot_hourly(self.hourly_ax, day_data, selected_date)
        self.hourly_fig.tight_layout()
        self.hourly_canvas.draw()

    def setup_monthly_monitoring_tab(self, parent):
        main_container = ttk.Frame(parent)
        main_container.pack(fill='both', expand=True, padx=10, pady=10)
        
        left_frame = ttk.Frame(main_container)
        left_frame.pack(side=tk.LEFT, fill='both', expand=True, padx=(0, 5))
        
        right_frame = ttk.Frame(main_container)
        right_frame.pack(side=tk.RIGHT, fill='both', expand=True, padx=(5, 0))
        
        control_frame = ttk.Frame(left_frame)
        control_frame.pack(fill='x', pady=(0, 10))
        
        ttk.Label(control_frame, text="Оберіть рік:").pack(side=tk.LEFT, padx=(0, 10))
        
        if self.df is not None:
            years = sorted(self.df['year'].unique())
            year_combo = ttk.Combobox(control_frame, textvariable=self.selected_year_monthly, 
                                    values=[str(y) for y in years], state="readonly", width=10)
            year_combo.pack(side=tk.LEFT, padx=(0, 20))
            year_combo.set(str(years[0]) if years else "")
        
        ttk.Button(control_frame, text="Оновити", command=self.update_monthly_monitoring).pack(side=tk.LEFT)
        
        graph_frame = ttk.LabelFrame(left_frame, text="Графік навантаження за рік", padding="5")
        graph_frame.pack(fill='both', expand=True)
        
        self.monthly_monitor_fig = Figure(figsize=(8, 6), dpi=100)
        self.monthly_monitor_ax = self.monthly_monitor_fig.add_subplot(111)
        
        self.monthly_monitor_canvas = FigureCanvasTkAgg(self.monthly_monitor_fig, graph_frame)
        self.monthly_monitor_canvas.get_tk_widget().pack(fill='both', expand=True)
        
        table_frame = ttk.LabelFrame(right_frame, text="Дані за рік", padding="5")
        table_frame.pack(fill='both', expand=True)
        
        columns = ("Місяць", "Макс. навантаження (МВт)", "Мін. навантаження (МВт)", 
                  "Середнє навантаження (МВт)", "Загальне споживання (МВт·год)")
        self.monthly_monitor_tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=20)
        
        for col in columns:
            self.monthly_monitor_tree.heading(col, text=col)
            self.monthly_monitor_tree.column(col, width=120)
        
        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.monthly_monitor_tree.yview)
        self.monthly_monitor_tree.configure(yscrollcommand=scrollbar.set)
        
        self.monthly_monitor_tree.pack(side=tk.LEFT, fill='both', expand=True)
        scrollbar.pack(side=tk.RIGHT, fill='y')
    
    def update_monthly_monitoring(self):
        if self.df is None:
            return
        
        try:
            selected_year = int(self.selected_year_monthly.get())
            year_data = self.df[self.df['year'] == selected_year]
            
            for item in self.monthly_monitor_tree.get_children():
                self.monthly_monitor_tree.delete(item)
            
            monthly_stats = year_data.groupby(['month', 'month_name']).agg({
                'load_mw': ['max', 'min', 'mean', 'sum']
            }).round(1)
            
            monthly_stats.columns = ['max_load', 'min_load', 'avg_load', 'total_consumption']
            monthly_stats = monthly_stats.sort_index(level='month')
            
            for (month, month_name), row in monthly_stats.iterrows():
                self.monthly_monitor_tree.insert("", "end", values=(
                    month_name,
                    f"{row['max_load']:.1f}",
                    f"{row['min_load']:.1f}",
                    f"{row['avg_load']:.1f}",
                    f"{row['total_consumption']:.0f}"
                ))
            
            self.update_monthly_monitor_plot(monthly_stats, selected_year)
            
        except Exception as e:
            messagebox.showerror("Помилка", f"Помилка при оновленні місячного моніторингу: {str(e)}")
    
    def update_monthly_monitor_plot(self, monthly_stats, year):
        plotting.plot_monthly_monitor(self.monthly_monitor_ax, monthly_stats, year)
        self.monthly_monitor_fig.tight_layout()
        self.monthly_monitor_canvas.draw()

    def setup_daily_consumption_tab(self, parent):
        main_container = ttk.Frame(parent)
        main_container.pack(fill='both', expand=True, padx=10, pady=10)
        
        left_frame = ttk.Frame(main_container)
        left_frame.pack(side=tk.LEFT, fill='both', expand=True, padx=(0, 5))
        
        right_frame = ttk.Frame(main_container)
        right_frame.pack(side=tk.RIGHT, fill='both', expand=True, padx=(5, 0))
        
        control_frame = ttk.Frame(left_frame)
        control_frame.pack(fill='x', pady=(0, 10))
        
        ttk.Label(control_frame, text="Оберіть рік:").pack(side=tk.LEFT, padx=(0, 10))
        
        if self.df is not None:
            years = sorted(self.df['year'].unique())
            year_combo = ttk.Combobox(control_frame, textvariable=self.selected_year_daily, 
                                    values=[str(y) for y in years], state="readonly", width=10)
            year_combo.pack(side=tk.LEFT, padx=(0, 20))
            year_combo.set(str(years[0]) if years else "")
        
        ttk.Label(control_frame, text="Місяць:").pack(side=tk.LEFT, padx=(0, 10))
        
        months = [("1", "Січень"), ("2", "Лютий"), ("3", "Березень"), ("4", "Квітень"),
                 ("5", "Травень"), ("6", "Червень"), ("7", "Липень"), ("8", "Серпень"),
                 ("9", "Вересень"), ("10", "Жовтень"), ("11", "Листопад"), ("12", "Грудень")]
        
        month_combo = ttk.Combobox(control_frame, textvariable=self.selected_month_daily, 
                                 values=[m[0] for m in months], state="readonly", width=10)
        month_combo.pack(side=tk.LEFT, padx=(0, 20))
        month_combo.set("1")
        
        ttk.Button(control_frame, text="Оновити", command=self.update_daily_consumption).pack(side=tk.LEFT)
        
        graphs_container = ttk.Frame(left_frame)
        graphs_container.pack(fill='both', expand=True)
        
        consumption_frame = ttk.LabelFrame(graphs_container, text="Графік споживання за день", padding="5")
        consumption_frame.pack(fill='both', expand=True, pady=(0, 5))
        
        self.daily_cons_fig = Figure(figsize=(8, 3), dpi=100)
        self.daily_cons_ax = self.daily_cons_fig.add_subplot(111)
        
        self.daily_cons_canvas = FigureCanvasTkAgg(self.daily_cons_fig, consumption_frame)
        self.daily_cons_canvas.get_tk_widget().pack(fill='both', expand=True)
        
        load_frame = ttk.LabelFrame(graphs_container, text="Графік навантаження за день", padding="5")
        load_frame.pack(fill='both', expand=True, pady=(5, 0))
        
        self.daily_load_fig = Figure(figsize=(8, 3), dpi=100)
        self.daily_load_ax = self.daily_load_fig.add_subplot(111)
        
        self.daily_load_canvas = FigureCanvasTkAgg(self.daily_load_fig, load_frame)
        self.daily_load_canvas.get_tk_widget().pack(fill='both', expand=True)
        
        table_frame = ttk.LabelFrame(right_frame, text="Дані за день", padding="5")
        table_frame.pack(fill='both', expand=True)
        
        columns = ("Дата", "Спожита енергія (МВт·год)", "Середнє навантаження (МВт)", 
                  "Максимальне навантаження (МВт)", "Тип дня")
        self.daily_cons_tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=20)
        
        for col in columns:
            self.daily_cons_tree.heading(col, text=col)
            self.daily_cons_tree.column(col, width=120)
        
        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.daily_cons_tree.yview)
        self.daily_cons_tree.configure(yscrollcommand=scrollbar.set)
        
        self.daily_cons_tree.pack(side=tk.LEFT, fill='both', expand=True)
        scrollbar.pack(side=tk.RIGHT, fill='y')
    
    def update_daily_consumption(self):
        for item in self.daily_cons_tree.get_children():
            self.daily_cons_tree.delete(item)
        
        try:
            selected_year = int(self.selected_year_daily.get())
            selected_month = int(self.selected_month_daily.get())
            
            month_data = self.df[
                (self.df['year'] == selected_year) & 
                (self.df['month'] == selected_month)
            ]
            
            if month_data.empty:
                messagebox.showwarning("Увага", "Немає даних за обраний період!")
                return
            
            daily_stats = month_data.groupby(['date', 'day_type']).agg({
                'load_mw': ['sum', 'mean', 'max']
            }).round(1)
            
            daily_stats.columns = ['total_energy', 'avg_load', 'max_load']
            daily_stats = daily_stats.sort_index(level='date')
            
            if daily_stats.empty:
                messagebox.showwarning("Увага", "Немає даних для побудови графіків!")
                return
            
            for (date, day_type), row in daily_stats.iterrows():
                self.daily_cons_tree.insert("", "end", values=(
                    str(date),
                    f"{row['total_energy']:.0f}",
                    f"{row['avg_load']:.1f}",
                    f"{row['max_load']:.1f}",
                    day_type
                ))
            
            month_name = month_data['month_name'].iloc[0] if len(month_data) > 0 else ""
            self.update_daily_consumption_plot(daily_stats, selected_year, month_name)
            self.update_daily_load_plot(daily_stats, selected_year, month_name)
            
        except Exception as e:
            messagebox.showerror("Помилка", f"Помилка при оновленні добового споживання: {str(e)}")
    
    def update_daily_consumption_plot(self, daily_stats, year, month_name):
        plotting.plot_daily_consumption(self.daily_cons_ax, daily_stats, year, month_name)
        self.daily_cons_fig.tight_layout()
        self.daily_cons_canvas.draw()
    
    def update_daily_load_plot(self, daily_stats, year, month_name):
        plotting.plot_daily_load(self.daily_load_ax, daily_stats, year, month_name)
        self.daily_load_fig.tight_layout()
        self.daily_load_canvas.draw()

    def setup_monthly_consumption_tab(self, parent):
        main_container = ttk.Frame(parent)
        main_container.pack(fill='both', expand=True, padx=10, pady=10)
        
        left_frame = ttk.Frame(main_container)
        left_frame.pack(side=tk.LEFT, fill='both', expand=True, padx=(0, 5))
        
        right_frame = ttk.Frame(main_container)
        right_frame.pack(side=tk.RIGHT, fill='both', expand=True, padx=(5, 0))
        
        graphs_container = ttk.Frame(left_frame)
        graphs_container.pack(fill='both', expand=True)
        
        consumption_frame = ttk.LabelFrame(graphs_container, text="Графік спожитої енергії за місяць", padding="5")
        consumption_frame.pack(fill='both', expand=True, pady=(0, 5))
        
        self.monthly_cons_fig = Figure(figsize=(8, 3), dpi=100)
        self.monthly_cons_ax = self.monthly_cons_fig.add_subplot(111)
        
        self.monthly_cons_canvas = FigureCanvasTkAgg(self.monthly_cons_fig, consumption_frame)
        self.monthly_cons_canvas.get_tk_widget().pack(fill='both', expand=True)
        
        load_frame = ttk.LabelFrame(graphs_container, text="Графік навантаження за місяць", padding="5")
        load_frame.pack(fill='both', expand=True, pady=(5, 0))
        
        self.monthly_load_fig = Figure(figsize=(8, 3), dpi=100)
        self.monthly_load_ax = self.monthly_load_fig.add_subplot(111)
        
        self.monthly_load_canvas = FigureCanvasTkAgg(self.monthly_load_fig, load_frame)
        self.monthly_load_canvas.get_tk_widget().pack(fill='both', expand=True)
        
        table_frame = ttk.LabelFrame(right_frame, text="Дані за місяць", padding="5")
        table_frame.pack(fill='both', expand=True)
        
        columns = ("Рік", "Місяць", "Спожита енергія (МВт·год)", "Середнє навантаження (МВт)", 
                  "Максимальне навантаження (МВт)", "Днів у місяці")
        self.monthly_cons_tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=20)
        
        for col in columns:
            self.monthly_cons_tree.heading(col, text=col)
            self.monthly_cons_tree.column(col, width=120)
        
        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.monthly_cons_tree.yview)
        self.monthly_cons_tree.configure(yscrollcommand=scrollbar.set)
        
        self.monthly_cons_tree.pack(side=tk.LEFT, fill='both', expand=True)
        scrollbar.pack(side=tk.RIGHT, fill='y')
    
    def update_monthly_consumption(self):
        for item in self.monthly_cons_tree.get_children():
            self.monthly_cons_tree.delete(item)
        
        try:
            monthly_consumption = self.df.groupby(['year', 'month_name', 'month']).agg({
                'load_mw': ['sum', 'mean', 'max'],
                'date': 'nunique'
            }).round(1)
            
            monthly_consumption.columns = ['total_energy', 'avg_load', 'max_load', 'days_count']
            monthly_consumption = monthly_consumption.sort_index(level=['year', 'month'])
            
            for (year, month_name, month), row in monthly_consumption.iterrows():
                self.monthly_cons_tree.insert("", "end", values=(
                    year,
                    month_name,
                    f"{row['total_energy']:.0f}",
                    f"{row['avg_load']:.1f}",
                    f"{row['max_load']:.1f}",
                    int(row['days_count'])
                ))
            
            self.update_monthly_consumption_plot(monthly_consumption)
            self.update_monthly_load_plot(monthly_consumption)
            
        except Exception as e:
            messagebox.showerror("Помилка", f"Помилка при оновленні місячного споживання: {str(e)}")
    
    def update_monthly_consumption_plot(self, monthly_consumption):
        plotting.plot_monthly_consumption(self.monthly_cons_ax, monthly_consumption)
        self.monthly_cons_fig.tight_layout()
        self.monthly_cons_canvas.draw()
    
    def update_monthly_load_plot(self, monthly_consumption):
        plotting.plot_monthly_load(self.monthly_load_ax, monthly_consumption)
        self.monthly_load_fig.tight_layout()
        self.monthly_load_canvas.draw()
    
    def update_all_pivot_tables(self):
        self.update_hourly_monitoring()
        self.update_monthly_monitoring()
        self.update_daily_consumption()
        self.update_monthly_consumption()

def main():
    root = tk.Tk()
    app = PowerLoadAnalysisApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
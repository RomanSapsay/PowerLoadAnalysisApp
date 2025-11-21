import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import os
import platform
import subprocess
import logging
import logic

class GenerationTab(ttk.Frame):
    def __init__(self, parent, app_context):
        super().__init__(parent)
        self.app = app_context
        self.pack(fill='both', expand=True)
        self.setup_ui()

    def setup_ui(self):
        # Основний контейнер
        main_card = ttk.Frame(self, style='Card.TFrame', padding=20)
        main_card.pack(fill='both', expand=True, padx=20, pady=20)
        
        # Заголовок
        header_frame = ttk.Frame(main_card, style='Card.TFrame')
        header_frame.pack(fill='x', pady=(0, 30))
        
        title_label = ttk.Label(header_frame, text="Генерація даних", 
                               font=('Segoe UI', 18, 'bold'), style='Card.TLabel')
        title_label.pack(side='left')
        
        # Ліва панель (Налаштування)
        content_frame = ttk.Frame(main_card, style='Card.TFrame')
        content_frame.pack(fill='both', expand=True)
        
        left_panel = ttk.LabelFrame(content_frame, text=" Налаштування ", padding=15)
        left_panel.pack(side='left', fill='both', expand=True, padx=(0, 10))
        
        grid_frame = ttk.Frame(left_panel, style='Card.TFrame')
        grid_frame.pack(fill='x')
        
        # Роки
        ttk.Label(grid_frame, text="Період:", style='Card.TLabel').grid(row=0, column=0, padx=5, pady=10, sticky='w')
        years_frame = ttk.Frame(grid_frame, style='Card.TFrame')
        years_frame.grid(row=0, column=1, padx=5, pady=10, sticky='w')
        ttk.Entry(years_frame, textvariable=self.app.start_year, width=6, justify='center').pack(side='left')
        ttk.Label(years_frame, text=" — ", style='Card.TLabel').pack(side='left')
        ttk.Entry(years_frame, textvariable=self.app.end_year, width=6, justify='center').pack(side='left')

        # Режим
        ttk.Label(grid_frame, text="Режим:", style='Card.TLabel').grid(row=1, column=0, padx=5, pady=10, sticky='w')
        mode_frame = ttk.Frame(grid_frame, style='Card.TFrame')
        mode_frame.grid(row=1, column=1, padx=5, pady=10, sticky='w')
        
        self.reproducible_btn = ttk.Button(mode_frame, text="Стандарт (Seed 42)", 
            command=lambda: self.set_random_mode("reproducible"))
        self.reproducible_btn.pack(side='left', padx=(0, 5))
        
        self.random_btn = ttk.Button(mode_frame, text="Випадковий", 
            command=lambda: self.set_random_mode("random"))
        self.random_btn.pack(side='left')

        # Папка
        ttk.Label(grid_frame, text="Папка:", style='Card.TLabel').grid(row=2, column=0, padx=5, pady=10, sticky='w')
        dir_frame = ttk.Frame(grid_frame, style='Card.TFrame')
        dir_frame.grid(row=2, column=1, padx=5, pady=10, sticky='ew')
        ttk.Entry(dir_frame, textvariable=self.app.output_dir, width=35).pack(side='left', padx=(0,5), fill='x', expand=True)
        ttk.Button(dir_frame, text="...", width=3, command=self.select_output_dir).pack(side='left')

        # Права панель (Дії)
        right_panel = ttk.Frame(content_frame, style='Card.TFrame')
        right_panel.pack(side='right', fill='both', expand=True, padx=(10, 0))
        
        action_frame = ttk.LabelFrame(right_panel, text=" Дії ", padding=15)
        action_frame.pack(fill='x', pady=(0, 20))
        
        self.generate_btn = ttk.Button(action_frame, text="▶ ЗАПУСТИТИ", 
                                     command=self.start_analysis, style='Accent.TButton')
        self.generate_btn.pack(fill='x', pady=(0, 10), ipady=5)
        
        ttk.Button(action_frame, text="Відкрити папку", command=self.open_results_dir).pack(fill='x')

        # Статус бар (замість великого тексту)
        status_frame = ttk.LabelFrame(right_panel, text=" Статус ", padding=15)
        status_frame.pack(fill='x', side='bottom')
        
        self.status_lbl = ttk.Label(status_frame, textvariable=self.app.status_text, 
                                  style='Card.TLabel', font=('Segoe UI', 9))
        self.status_lbl.pack(anchor='w', pady=(0, 5))
        
        self.progress_bar = ttk.Progressbar(status_frame, variable=self.app.progress, maximum=100)
        self.progress_bar.pack(fill='x')

        self.update_mode_buttons()

    def set_random_mode(self, mode):
        self.app.random_mode.set(mode)
        self.update_mode_buttons()
        logging.info(f"Режим змінено на: {mode}")

    def update_mode_buttons(self):
        mode = self.app.random_mode.get()
        if mode == "reproducible":
            self.reproducible_btn.state(['pressed'])
            self.random_btn.state(['!pressed'])
        else:
            self.reproducible_btn.state(['!pressed'])
            self.random_btn.state(['pressed'])

    def select_output_dir(self):
        directory = filedialog.askdirectory(initialdir=self.app.output_dir.get())
        if directory:
            self.app.output_dir.set(directory)

    def open_results_dir(self):
        path = os.path.abspath(self.app.output_dir.get())
        if os.path.exists(path):
            try:
                if platform.system() == "Windows": os.startfile(path)
                elif platform.system() == "Darwin": subprocess.call(["open", path])
                else: subprocess.call(["xdg-open", path])
            except Exception: pass
        else:
            messagebox.showwarning("Увага", "Папка ще не створена.")

    def start_analysis(self):
        try:
            s_year = int(self.app.start_year.get())
            e_year = int(self.app.end_year.get())
            if s_year > e_year: raise ValueError
            
            self.generate_btn.config(state='disabled')
            self.app.status_text.set("Обробка...")
            
            thread = threading.Thread(target=self.run_analysis_thread, args=(s_year, e_year))
            thread.daemon = True
            thread.start()
        except ValueError:
            messagebox.showerror("Помилка", "Перевірте роки")

    def run_analysis_thread(self, start_year, end_year):
        try:
            self.update_progress_safe(10, "Ініціалізація...")
            seed = 42 if self.app.random_mode.get() == "reproducible" else None
            
            raw_df = logic.generate_power_load_data(start_year, end_year, seed)
            self.update_progress_safe(50, "Обчислення...")
            processed_df = logic.prepare_data(raw_df)
            
            self.update_progress_safe(80, "Збереження...")
            logic.create_csv_reports(processed_df, self.app.output_dir.get(), self.app.random_mode.get())
            
            self.update_progress_safe(100, "Готово")
            self.app.root.after(0, lambda: self.finish_success(processed_df))
            
        except Exception as e:
            self.app.root.after(0, lambda: self.finish_error(str(e)))

    def update_progress_safe(self, val, msg):
        self.app.root.after(0, lambda: self._update_prog(val, msg))

    def _update_prog(self, val, msg):
        self.app.progress.set(val)
        self.app.status_text.set(msg)

    def finish_success(self, df):
        self.app.df = df
        self.app.refresh_all_tabs()
        self.app.status_text.set("Симуляцію завершено")
        self.generate_btn.config(state='normal')
        # Стандартне Windows повідомлення
        messagebox.showinfo("Успіх", f"Дані успішно згенеровано!\nВсього записів: {len(df)}")

    def finish_error(self, error_msg):
        self.app.status_text.set("Помилка")
        self.generate_btn.config(state='normal')
        messagebox.showerror("Помилка", str(error_msg))

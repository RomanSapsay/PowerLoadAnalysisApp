import tkinter as tk
from tkinter import ttk, messagebox
import os
import sys
import logging
import matplotlib

# Налаштування шрифтів для графіків
matplotlib.rcParams['font.family'] = 'DejaVu Sans'

# Імпорт наших модулів
from ui_generation import GenerationTab
from ui_analysis import HourlyTab, MonthlyMonitorTab, DailyConsumptionTab, MonthlyConsumptionTab

# --- НАЛАШТУВАННЯ ЛОГУВАННЯ (PROFESSIONAL LOGGING) ---
logging.basicConfig(
    filename='energy_system.log',
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(module)s:%(lineno)d | %(message)s',
    encoding='utf-8',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# Дублюємо логи в консоль (для розробника)
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s | %(levelname)s | %(message)s')
console_handler.setFormatter(formatter)
logging.getLogger().addHandler(console_handler)

class PowerLoadAnalysisApp:
    def __init__(self, root):
        logging.info("=== ЗАПУСК СИСТЕМИ ENERGY MONITOR PRO ===")
        self.root = root
        self.root.title("Energy Monitor Pro v2.1 [Enterprise Edition]")
        self.root.geometry("1280x850")
        
        # Обробка закриття вікна (щоб записати лог виходу)
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        
        # --- КОЛЬОРОВА ПАЛІТРА (Dark Theme) ---
        self.colors = {
            'bg_dark': '#1e1e1e',
            'bg_lighter': '#2d2d2d',
            'accent': '#00e5ff',
            'text': '#ffffff',
            'text_dim': '#aaaaaa',
            'success': '#00e676',
            'warning': '#ffea00',
            'danger': '#ff1744'
        }

        self.root.configure(bg=self.colors['bg_dark'])
        self.setup_styles()
        
        # --- СТАН ДОДАТКУ (STATE) ---
        self.df = None
        self.start_year = tk.StringVar(value="2024")
        self.end_year = tk.StringVar(value="2024")
        self.random_mode = tk.StringVar(value="reproducible")
        
        # Автоматично створюємо папку results, якщо немає
        default_dir = os.path.join(os.getcwd(), "results")
        if not os.path.exists(default_dir):
            os.makedirs(default_dir)
            logging.info(f"Створено директорію за замовчуванням: {default_dir}")
            
        self.output_dir = tk.StringVar(value=default_dir)
        
        self.progress = tk.DoubleVar()
        self.status_text = tk.StringVar(value="Система готова. Очікування команд оператора.")
        self.result_text = tk.StringVar(value="")

        # --- ІНТЕРФЕЙС ---
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=10)

        # Вкладка 1: Генерація
        self.gen_tab = GenerationTab(self.notebook, self)
        self.notebook.add(self.gen_tab, text="⚙️ КЕРУВАННЯ")

        # Вкладки 2-5: Аналітика
        self.analysis_tabs = [
            HourlyTab(self.notebook, self),
            MonthlyMonitorTab(self.notebook, self),
            DailyConsumptionTab(self.notebook, self),
            MonthlyConsumptionTab(self.notebook, self)
        ]
        
        titles = ["📈 Погодинний аналіз", "📊 Місячний звіт", "📅 Добове споживання", "📆 Річна статистика"]
        for tab, title in zip(self.analysis_tabs, titles):
            self.notebook.add(tab, text=title)

    def setup_styles(self):
        """Налаштування стилів інтерфейсу (CSS-like)"""
        style = ttk.Style()
        style.theme_use('clam')

        # Базові кольори
        style.configure('.', 
            background=self.colors['bg_dark'], 
            foreground=self.colors['text'],
            fieldbackground=self.colors['bg_lighter'],
            font=('Segoe UI', 10)
        )

        # Вкладки
        style.configure('TNotebook', background=self.colors['bg_dark'], borderwidth=0)
        style.configure('TNotebook.Tab', 
            background=self.colors['bg_lighter'], 
            foreground=self.colors['text'],
            padding=[20, 8],
            font=('Segoe UI', 10, 'bold')
        )
        style.map('TNotebook.Tab', 
            background=[('selected', self.colors['accent'])],
            foreground=[('selected', '#000000')]
        )

        # Контейнери
        style.configure('TFrame', background=self.colors['bg_dark'])
        style.configure('Card.TFrame', background=self.colors['bg_lighter'], relief='flat')
        
        # Рамки з підписами
        style.configure('TLabelframe', 
            background=self.colors['bg_lighter'], 
            foreground=self.colors['accent'],
            bordercolor='#444444'
        )
        style.configure('TLabelframe.Label', 
            background=self.colors['bg_lighter'], 
            foreground=self.colors['accent'],
            font=('Segoe UI', 11, 'bold')
        )

        # Кнопки (стандартні та акцентні)
        style.configure('TButton', 
            background='#333333',
            foreground=self.colors['accent'],
            borderwidth=1,
            focuscolor='none',
            font=('Segoe UI', 10, 'bold')
        )
        style.map('TButton', 
            background=[('active', '#444444'), ('pressed', self.colors['accent'])], 
            foreground=[('pressed', '#000000')]
        )
        
        style.configure('Accent.TButton', 
            background=self.colors['accent'],
            foreground='#000000',
            font=('Segoe UI', 11, 'bold')
        )
        style.map('Accent.TButton', background=[('active', self.colors['success'])])

        # Таблиці
        style.configure("Treeview",
            background=self.colors['bg_lighter'],
            foreground=self.colors['text'],
            fieldbackground=self.colors['bg_lighter'],
            borderwidth=0,
            rowheight=30,
            font=('Consolas', 10)
        )
        style.configure("Treeview.Heading",
            background='#252525',
            foreground=self.colors['accent'],
            font=('Segoe UI', 9, 'bold'),
            relief="flat"
        )
        style.map("Treeview", background=[('selected', self.colors['accent'])], foreground=[('selected', '#000000')])

        # Текстові мітки
        style.configure('TLabel', background=self.colors['bg_dark'], foreground=self.colors['text'])
        style.configure('Card.TLabel', background=self.colors['bg_lighter'], foreground=self.colors['text'])

    def refresh_all_tabs(self):
        """Оновлення даних у всіх вкладках після генерації"""
        logging.info("Оновлення інтерфейсу (refresh_all_tabs)...")
        for tab in self.analysis_tabs:
            if hasattr(tab, 'update_controls_state'):
                tab.update_controls_state()
            if hasattr(tab, 'update_data'):
                tab.update_data()

    def on_close(self):
        logging.info("=== ЗАВЕРШЕННЯ РОБОТИ ===")
        self.root.destroy()

if __name__ == "__main__":
    try:
        root = tk.Tk()
        app = PowerLoadAnalysisApp(root)
        root.mainloop()
    except Exception as e:
        logging.critical(f"Критична помилка при запуску: {e}", exc_info=True)

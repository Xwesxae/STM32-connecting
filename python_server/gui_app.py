import tkinter as tk
from tkinter import ttk, messagebox
import threading
from datetime import datetime
from database import STM32Database
from network_server import STM32Server

class STM32ManagerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("STM32 Manager v1.0")
        self.root.geometry("1000x700")
        
        # Инициализация базы данных и сервера
        self.db = STM32Database("stm32_data.db")
        self.server = STM32Server("0.0.0.0", 8080, self.db)
        
        self.setup_ui()
        self.start_server()
    
    def setup_ui(self):
        """Настройка пользовательского интерфейса"""
        # Основные фреймы
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Левая панель - управление
        left_frame = ttk.Frame(main_frame)
        left_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 10))
        
        # Правая панель - данные
        right_frame = ttk.Frame(main_frame)
        right_frame.grid(row=0, column=1, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(0, weight=1)
        
        # Панель подключенных устройств
        self.setup_devices_panel(left_frame)
        
        # Панель команд
        self.setup_commands_panel(left_frame)
        
        # Панель данных
        self.setup_data_panel(right_frame)
        
        # Статус бар
        self.setup_status_bar()
    
    def setup_devices_panel(self, parent):
        """Панель подключенных устройств"""
        devices_frame = ttk.LabelFrame(parent, text="Подключенные устройства", padding="5")
        devices_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        
        # Список устройств
        self.devices_listbox = tk.Listbox(devices_frame, height=8)
        self.devices_listbox.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Кнопка обновления
        ttk.Button(devices_frame, text="Обновить", 
                  command=self.refresh_devices).grid(row=1, column=0, pady=5)
        
        devices_frame.columnconfigure(0, weight=1)
        devices_frame.rowconfigure(0, weight=1)
    
    def setup_commands_panel(self, parent):
        """Панель отправки команд"""
        commands_frame = ttk.LabelFrame(parent, text="Управление STM32", padding="5")
        commands_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Выбор команды
        ttk.Label(commands_frame, text="Команда:").grid(row=0, column=0, sticky=tk.W)
        self.command_var = tk.StringVar()
        command_combo = ttk.Combobox(commands_frame, textvariable=self.command_var,
                                   values=["READ_SENSORS", "SET_LED", "SET_MOTOR", "REBOOT"])
        command_combo.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(5, 0))
        
        # Параметры
        ttk.Label(commands_frame, text="Параметры:").grid(row=1, column=0, sticky=tk.W, pady=(5, 0))
        self.parameters_entry = ttk.Entry(commands_frame)
        self.parameters_entry.grid(row=1, column=1, sticky=(tk.W, tk.E), padx=(5, 0), pady=(5, 0))
        
        # Кнопка отправки
        ttk.Button(commands_frame, text="Отправить команду",
                  command=self.send_command).grid(row=2, column=0, columnspan=2, pady=10)
        
        commands_frame.columnconfigure(1, weight=1)
    
    def setup_data_panel(self, parent):
        """Панель отображения данных"""
        # Таблица данных
        columns = ("timestamp", "address", "sensor_type", "value")
        self.data_tree = ttk.Treeview(parent, columns=columns, show="headings", height=15)
        
        # Заголовки
        self.data_tree.heading("timestamp", text="Время")
        self.data_tree.heading("address", text="Адрес")
        self.data_tree.heading("sensor_type", text="Тип сенсора")
        self.data_tree.heading("value", text="Значение")
        
        self.data_tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Скроллбар
        scrollbar = ttk.Scrollbar(parent, orient=tk.VERTICAL, command=self.data_tree.yview)
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        self.data_tree.configure(yscrollcommand=scrollbar.set)
        
        # Кнопки управления данными
        button_frame = ttk.Frame(parent)
        button_frame.grid(row=1, column=0, columnspan=2, pady=5)
        
        ttk.Button(button_frame, text="Обновить данные", 
                  command=self.refresh_data).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Экспорт в CSV", 
                  command=self.export_to_csv).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Очистить историю", 
                  command=self.clear_history).pack(side=tk.LEFT, padx=5)
        
        parent.columnconfigure(0, weight=1)
        parent.rowconfigure(0, weight=1)
    
    def setup_status_bar(self):
        """Строка статуса"""
        self.status_var = tk.StringVar(value="Готов")
        status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN)
        status_bar.grid(row=1, column=0, sticky=(tk.W, tk.E))
    
    def start_server(self):
        """Запуск сервера в отдельном потоке"""
        def server_thread():
            try:
                self.server.start()
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось запустить сервер: {e}")
        
        thread = threading.Thread(target=server_thread, daemon=True)
        thread.start()
        self.status_var.set("Сервер запущен на порту 8080")
    
    def refresh_devices(self):
        """Обновление списка устройств"""
        self.devices_listbox.delete(0, tk.END)
        for client_id in self.server.clients.keys():
            self.devices_listbox.insert(tk.END, client_id)
    
    def send_command(self):
        """Отправка команды выбранному устройству"""
        selection = self.devices_listbox.curselection()
        if not selection:
            messagebox.showwarning("Предупреждение", "Выберите устройство")
            return
        
        client_id = self.devices_listbox.get(selection[0])
        command_type = self.command_var.get()
        parameters = self.parameters_entry.get()
        
        if not command_type:
            messagebox.showwarning("Предупреждение", "Выберите тип команды")
            return
        
        try:
            command_id = self.server.send_immediate_command(client_id, command_type, parameters)
            self.status_var.set(f"Команда {command_id} отправлена к {client_id}")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка отправки команды: {e}")
    
    def refresh_data(self):
        """Обновление таблицы данных"""
        for item in self.data_tree.get_children():
            self.data_tree.delete(item)
        
        # Получение данных из базы
        data = self.db.get_sensor_data("all", 100)  # Последние 100 записей
        
        for row in data:
            self.data_tree.insert("", 0, values=(
                row['timestamp'],
                row['stm32_address'],
                row['sensor_type'],
                row['value']
            ))
    
    def export_to_csv(self):
        """Экспорт данных в CSV"""
        try:
            from datetime import datetime
            filename = f"stm32_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            
            with open(filename, 'w', encoding='utf-8') as f:
                f.write("Timestamp,Address,SensorType,Value\n")
                data = self.db.get_sensor_data("all", 1000)
                for row in data:
                    f.write(f"{row['timestamp']},{row['stm32_address']},{row['sensor_type']},{row['value']}\n")
            
            self.status_var.set(f"Данные экспортированы в {filename}")
            messagebox.showinfo("Успех", f"Данные экспортированы в {filename}")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка экспорта: {e}")
    
    def clear_history(self):
        """Очистка истории данных"""
        if messagebox.askyesno("Подтверждение", "Очистить всю историю данных?"):
            try:
                with sqlite3.connect(self.db.db_path) as conn:
                    cursor = conn.cursor()
                    cursor.execute("DELETE FROM stm32_data")
                    conn.commit()
                self.refresh_data()
                self.status_var.set("История данных очищена")
            except Exception as e:
                messagebox.showerror("Ошибка", f"Ошибка очистки: {e}")

def main():
    root = tk.Tk()
    app = STM32ManagerApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
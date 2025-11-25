import sqlite3
import logging
from datetime import datetime
from typing import List, Dict, Optional

class STM32Database:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Инициализация базы данных"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Таблица для данных с микроконтроллера
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS stm32_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    stm32_address TEXT NOT NULL,
                    sensor_type TEXT NOT NULL,
                    value REAL NOT NULL,
                    raw_data BLOB,
                    status TEXT DEFAULT 'received'
                )
            ''')
            
            # Таблица для команд управления
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS commands (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    stm32_address TEXT NOT NULL,
                    command_type TEXT NOT NULL,
                    parameters TEXT,
                    status TEXT DEFAULT 'pending',
                    executed_at DATETIME,
                    response TEXT
                )
            ''')
            
            # Таблица для логов соединений
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS connections (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    stm32_address TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    details TEXT
                )
            ''')
            
            conn.commit()
    
    def save_sensor_data(self, address: str, sensor_type: str, value: float, raw_data: bytes = None):
        """Сохранение данных от STM32"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO stm32_data (stm32_address, sensor_type, value, raw_data)
                VALUES (?, ?, ?, ?)
            ''', (address, sensor_type, value, raw_data))
            conn.commit()
            return cursor.lastrowid
    
    def save_command(self, address: str, command_type: str, parameters: str = None) -> int:
        """Сохранение команды для STM32"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO commands (stm32_address, command_type, parameters)
                VALUES (?, ?, ?)
            ''', (address, command_type, parameters))
            conn.commit()
            return cursor.lastrowid
    
    def update_command_status(self, command_id: int, status: str, response: str = None):
        """Обновление статуса команды"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            executed_at = datetime.now().isoformat() if status == 'executed' else None
            cursor.execute('''
                UPDATE commands 
                SET status = ?, response = ?, executed_at = ?
                WHERE id = ?
            ''', (status, response, executed_at, command_id))
            conn.commit()
    
    def get_pending_commands(self, address: str) -> List[Dict]:
        """Получение ожидающих команд для STM32"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM commands 
                WHERE stm32_address = ? AND status = 'pending'
                ORDER BY timestamp
            ''', (address,))
            return [dict(row) for row in cursor.fetchall()]
    
    def get_sensor_data(self, address: str, limit: int = 100) -> List[Dict]:
        """Получение исторических данных"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM stm32_data 
                WHERE stm32_address = ?
                ORDER BY timestamp DESC
                LIMIT ?
            ''', (address, limit))
            return [dict(row) for row in cursor.fetchall()]
    
    def log_connection_event(self, address: str, event_type: str, details: str = None):
        """Логирование событий соединения"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO connections (stm32_address, event_type, details)
                VALUES (?, ?, ?)
            ''', (address, event_type, details))
            conn.commit()
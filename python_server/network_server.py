import socket
import threading
import json
import logging
from datetime import datetime
from database import STM32Database

class STM32Server:
    def __init__(self, host: str, port: int, db: STM32Database):
        self.host = host
        self.port = port
        self.db = db
        self.clients = {}  # address -> (socket, thread)
        self.running = False
        self.server_socket = None
        
    def start(self):
        """Запуск сервера"""
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(5)
        
        self.running = True
        logging.info(f"Сервер запущен на {self.host}:{self.port}")
        
        # Поток для принятия подключений
        accept_thread = threading.Thread(target=self._accept_connections)
        accept_thread.daemon = True
        accept_thread.start()
        
        # Поток для отправки команд
        command_thread = threading.Thread(target=self._command_dispatcher)
        command_thread.daemon = True
        command_thread.start()
    
    def _accept_connections(self):
        """Принятие входящих подключений"""
        while self.running:
            try:
                client_socket, address = self.server_socket.accept()
                client_thread = threading.Thread(
                    target=self._handle_client,
                    args=(client_socket, address)
                )
                client_thread.daemon = True
                client_thread.start()
                
                logging.info(f"Подключен клиент: {address}")
                self.db.log_connection_event(str(address), "connected")
                
            except Exception as e:
                if self.running:
                    logging.error(f"Ошибка принятия соединения: {e}")
    
    def _handle_client(self, client_socket: socket.socket, address: tuple):
        """Обработка клиентского соединения"""
        client_id = f"{address[0]}:{address[1]}"
        self.clients[client_id] = client_socket
        
        try:
            while self.running:
                data = client_socket.recv(4096)
                if not data:
                    break
                
                self._process_client_data(client_id, data)
                
        except Exception as e:
            logging.error(f"Ошибка обработки клиента {client_id}: {e}")
        finally:
            if client_id in self.clients:
                del self.clients[client_id]
            client_socket.close()
            self.db.log_connection_event(client_id, "disconnected")
            logging.info(f"Клиент отключен: {client_id}")
    
    def _process_client_data(self, client_id: str, data: bytes):
        """Обработка данных от клиента"""
        try:
            message = data.decode('utf-8').strip()
            
            # Попытка парсинга JSON
            try:
                json_data = json.loads(message)
                self._process_json_message(client_id, json_data)
            except json.JSONDecodeError:
                # Обработка простого текстового протокола
                self._process_text_message(client_id, message)
                
        except Exception as e:
            logging.error(f"Ошибка обработки данных от {client_id}: {e}")
    
    def _process_json_message(self, client_id: str, data: dict):
        """Обработка JSON сообщений"""
        message_type = data.get('type')
        
        if message_type == 'sensor_data':
            # Сохранение данных сенсоров
            for sensor_type, value in data.get('data', {}).items():
                self.db.save_sensor_data(client_id, sensor_type, value)
            logging.info(f"Данные от {client_id}: {data['data']}")
            
        elif message_type == 'command_response':
            # Обновление статуса команды
            command_id = data.get('command_id')
            response = data.get('response')
            self.db.update_command_status(command_id, 'executed', response)
            
        elif message_type == 'status':
            # Обработка статуса устройства
            self.db.log_connection_event(client_id, 'status_update', str(data))
    
    def _process_text_message(self, client_id: str, message: str):
        """Обработка текстовых сообщений"""
        if message.startswith('SENSOR:'):
            # Формат: SENSOR:TYPE:VALUE
            parts = message.split(':')
            if len(parts) >= 3:
                sensor_type = parts[1]
                value = float(parts[2])
                self.db.save_sensor_data(client_id, sensor_type, value)
                logging.info(f"Текстовые данные от {client_id}: {sensor_type}={value}")
    
    def _command_dispatcher(self):
        """Отправка ожидающих команд клиентам"""
        while self.running:
            try:
                for client_id in list(self.clients.keys()):
                    pending_commands = self.db.get_pending_commands(client_id)
                    
                    for command in pending_commands:
                        self._send_command_to_client(client_id, command)
                
                threading.Event().wait(1)  # Пауза 1 секунда
                
            except Exception as e:
                logging.error(f"Ошибка диспетчера команд: {e}")
    
    def _send_command_to_client(self, client_id: str, command: dict):
        """Отправка команды конкретному клиенту"""
        try:
            if client_id in self.clients:
                client_socket = self.clients[client_id]
                
                command_message = json.dumps({
                    'command_id': command['id'],
                    'type': command['command_type'],
                    'parameters': command['parameters']
                })
                
                client_socket.send((command_message + '\n').encode('utf-8'))
                logging.info(f"Отправлена команда {command['id']} к {client_id}")
                
        except Exception as e:
            logging.error(f"Ошибка отправки команды к {client_id}: {e}")
            self.db.update_command_status(command['id'], 'failed', str(e))
    
    def send_immediate_command(self, client_id: str, command_type: str, parameters: str = None) -> int:
        """Немедленная отправка команды"""
        command_id = self.db.save_command(client_id, command_type, parameters)
        return command_id
    
    def stop(self):
        """Остановка сервера"""
        self.running = False
        if self.server_socket:
            self.server_socket.close()
        
        for client_socket in self.clients.values():
            try:
                client_socket.close()
            except:
                pass
        self.clients.clear()
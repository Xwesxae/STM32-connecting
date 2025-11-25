# -*- coding: utf-8 -*-
import socket
import time

print("🚀 Simple STM32 Client Test")

# Создаем новое соединение для КАЖДОГО сообщения
def send_sensor_data(sensor_type, value):
    try:
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.settimeout(5)  # Таймаут 5 секунд
        client.connect(('localhost', 8080))
        
        message = f"SENSOR:{sensor_type}:{value}\n"
        client.send(message.encode())
        print(f"✅ Sent: {message.strip()}")
        
        client.close()
        return True
        
    except Exception as e:
        print(f"❌ Failed to send {sensor_type}: {e}")
        return False

# Отправляем тестовые данные
send_sensor_data("TEMPERATURE", 25.5)
time.sleep(1)

send_sensor_data("HUMIDITY", 60.2) 
time.sleep(1)

send_sensor_data("PRESSURE", 1013.25)
time.sleep(1)

send_sensor_data("VOLTAGE", 3.3)

print("🎉 All test data sent!")
# -*- coding: utf-8 -*-
import socket
import time
import random

print("🧪 Test Client")

try:
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect(('localhost', 8080))
    
    print("✅ Connected to server!")

    for i in range(3):
        # Генерируем тестовые данные
        temp = 20 + random.random() * 10
        hum = 40 + random.random() * 30
        
        try:
            # Отправляем температуру
            message1 = f"SENSOR:TEMPERATURE:{temp:.1f}\n"
            client.send(message1.encode())
            print(f"📤 Sent: {message1.strip()}")
            time.sleep(0.5)  # Небольшая пауза
            
            # Отправляем влажность
            message2 = f"SENSOR:HUMIDITY:{hum:.1f}\n"
            client.send(message2.encode())
            print(f"📤 Sent: {message2.strip()}")
            time.sleep(1)  # Пауза между наборами данных
            
        except (BrokenPipeError, ConnectionAbortedError, ConnectionResetError):
            print("❌ Connection lost")
            break
            
    client.close()
    print("✅ Test completed!")
    
except ConnectionRefusedError:
    print("❌ Server not running! Start main.py first")
except Exception as e:
    print(f"❌ Error: {e}")
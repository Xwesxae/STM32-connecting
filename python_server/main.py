# -*- coding: utf-8 -*-
import socket
import sqlite3
import threading
import time

print("STM32 Server Starting...")

# Create database
conn = sqlite3.connect('stm32_data.db', check_same_thread=False)
cursor = conn.cursor()
cursor.execute('''
    CREATE TABLE IF NOT EXISTS sensor_data (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        address TEXT,
        sensor_type TEXT,
        value REAL
    )
''')
conn.commit()
print("Database created")

clients = {}
running = True

def handle_client(client_socket, address):
    client_id = f"{address[0]}:{address[1]}"
    clients[client_id] = client_socket
    print(f"Client connected: {client_id}")
    
    try:
        while running:
            data = client_socket.recv(1024)
            if not data:
                break
                
            message = data.decode('utf-8').strip()
            print(f"Received from {client_id}: {message}")
            
            # Save to database
            if message.startswith('SENSOR:'):
                parts = message.split(':')
                if len(parts) >= 3:
                    sensor_type = parts[1]
                    value = float(parts[2])
                    
                    cursor.execute(
                        "INSERT INTO sensor_data (address, sensor_type, value) VALUES (?, ?, ?)",
                        (client_id, sensor_type, value)
                    )
                    conn.commit()
                    print(f"Saved: {sensor_type} = {value}")
                    
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if client_id in clients:
            del clients[client_id]
        client_socket.close()
        print(f"Client disconnected: {client_id}")

# Start server
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind(('0.0.0.0', 8080))
server_socket.listen(5)
print("Server started on port 8080")

# Accept connections in separate thread
def accept_connections():
    while running:
        try:
            client_socket, address = server_socket.accept()
            client_thread = threading.Thread(target=handle_client, args=(client_socket, address))
            client_thread.daemon = True
            client_thread.start()
        except:
            break

accept_thread = threading.Thread(target=accept_connections)
accept_thread.daemon = True
accept_thread.start()

print("Server is running. Press Ctrl+C to stop.")

try:
    # Simple menu
    while True:
        print("\nOptions: 1=Show data, 2=Show clients, 3=Exit")
        choice = input("Choose: ").strip()
        
        if choice == '1':
            cursor.execute("SELECT * FROM sensor_data ORDER BY timestamp DESC LIMIT 5")
            rows = cursor.fetchall()
            print("\nLast 5 records:")
            for row in rows:
                print(f"ID: {row[0]}, Time: {row[1]}, Addr: {row[2]}, Sensor: {row[3]}, Value: {row[4]}")
                
        elif choice == '2':
            print(f"Connected clients: {list(clients.keys())}")
            
        elif choice == '3':
            break
            
        else:
            print("Invalid choice")
            
except KeyboardInterrupt:
    print("\nStopping server...")
finally:
    running = False
    server_socket.close()
    conn.close()
    print("Server stopped")
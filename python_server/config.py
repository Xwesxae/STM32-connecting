import os
from dataclasses import dataclass

@dataclass
class Config:
    DB_PATH = "stm32_data.db"
    SERVER_HOST = "0.0.0.0"
    SERVER_PORT = 8080
    BUFFER_SIZE = 4096

config = Config()
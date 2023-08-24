"""Файл содержит конфигурации сервиса"""
import sys

from loguru import logger

logger.remove(0)
logger.add(
    'debug.log',
    format='{time} {level} {message}',
    level="DEBUG",
    encoding='utf-8'
)


config = {
    'handlers': [
        {
            'sink': './logs/debug.log',  # запись логов в файл debug.log
            'format': '{time} {level} {file} {line} {message}',
            'level': "DEBUG",
            'encoding': 'utf-8',
            'rotation': '1 month',  # устанавливаем ротацию debug.json_co каждый месяц
            'compression': 'zip',  # архивирует старые debug.json_co файлы
        },
        {
            'sink': sys.stdout,  # вывод сообщений об ошибках в консоль
            'colorize': True,
            'format': '{time} {level} {file} {line} {message}'
        }
        # {'sink': my_sink,
        #  'level': "ERROR",
        #  'serialize': True,
        #  }
    ],
}

logger.configure(**config)

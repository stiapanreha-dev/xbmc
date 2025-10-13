#!/usr/bin/env python3
"""
Проверка структуры таблиц db_companies, db_rubrics, db_subrubrics, db_cities
"""
import os
from dotenv import load_dotenv
import pymssql

load_dotenv()

# MSSQL настройки
server = os.getenv('MSSQL_SERVER')
user = os.getenv('MSSQL_USER')
password = os.getenv('MSSQL_PASSWORD')
database = os.getenv('MSSQL_DATABASE')

try:
    conn = pymssql.connect(server=server, user=user, password=password, database=database)
    cursor = conn.cursor()

    tables = ['db_companies', 'db_rubrics', 'db_subrubrics', 'db_cities']

    for table in tables:
        print(f"\n{'='*60}")
        print(f"Структура таблицы: {table}")
        print('='*60)

        # Получаем структуру таблицы
        cursor.execute(f"""
            SELECT
                COLUMN_NAME,
                DATA_TYPE,
                CHARACTER_MAXIMUM_LENGTH,
                IS_NULLABLE
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_NAME = '{table}'
            ORDER BY ORDINAL_POSITION
        """)

        print(f"{'Колонка':<30} {'Тип':<20} {'Размер':<10} {'NULL':<5}")
        print('-'*60)

        for row in cursor.fetchall():
            col_name, data_type, max_length, nullable = row
            max_length_str = str(max_length) if max_length else ''
            print(f"{col_name:<30} {data_type:<20} {max_length_str:<10} {nullable:<5}")

        # Получаем количество записей
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        count = cursor.fetchone()[0]
        print(f"\nВсего записей: {count}")

        # Получаем пример данных (первые 3 строки)
        cursor.execute(f"SELECT TOP 3 * FROM {table}")
        print(f"\nПример данных:")
        rows = cursor.fetchall()
        if rows:
            columns = [desc[0] for desc in cursor.description]
            print(f"Колонки: {', '.join(columns)}")
            for i, row in enumerate(rows, 1):
                print(f"Строка {i}: {row}")

    conn.close()
    print("\n" + "="*60)
    print("Проверка завершена успешно!")
    print("="*60)

except Exception as e:
    print(f"Ошибка: {e}")

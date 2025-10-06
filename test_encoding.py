#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pymssql
import os
from dotenv import load_dotenv

load_dotenv()

server = os.getenv('MSSQL_SERVER', '172.26.192.1')
user = os.getenv('MSSQL_USER', 'sa')
password = os.getenv('MSSQL_PASSWORD', '123123123')
database = os.getenv('MSSQL_DATABASE', 'business')
port = int(os.getenv('MSSQL_PORT', '1433'))

print("Testing different charset options...\n")

charsets = ['utf8', 'UTF-8', 'cp1251', 'windows-1251', None]

for charset in charsets:
    try:
        print(f"Trying charset: {charset}")

        if charset:
            conn = pymssql.connect(
                server=server,
                user=user,
                password=password,
                database=database,
                port=port,
                charset=charset
            )
        else:
            conn = pymssql.connect(
                server=server,
                user=user,
                password=password,
                database=database,
                port=port
            )

        cursor = conn.cursor(as_dict=True)
        cursor.execute("SELECT TOP 1 purchase_object, customer FROM zakupki WHERE purchase_object IS NOT NULL")
        result = cursor.fetchone()

        if result:
            print(f"  purchase_object: {result['purchase_object'][:50]}")
            print(f"  customer: {result['customer'][:50]}")

        conn.close()
        print(f"  ✓ Success\n")

    except Exception as e:
        print(f"  ✗ Error: {e}\n")

print("\nТест завершен. Найдите вариант с правильной кириллицей.")

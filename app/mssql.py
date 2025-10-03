import pymssql
import os
from datetime import datetime

class MSSQLConnection:
    def __init__(self):
        self.server = os.getenv('MSSQL_SERVER', '172.26.192.1')
        self.user = os.getenv('MSSQL_USER', 'sa')
        self.password = os.getenv('MSSQL_PASSWORD', '123123123')
        self.database = os.getenv('MSSQL_DATABASE', 'buss')
        self.port = int(os.getenv('MSSQL_PORT', '1433'))

    def get_connection(self):
        return pymssql.connect(
            server=self.server,
            user=self.user,
            password=self.password,
            database=self.database,
            port=self.port
        )

    def get_zakupki(self, date_from=None, date_to=None, search_text=None, limit=100, offset=0):
        """Получить закупки с фильтрацией"""
        conn = self.get_connection()
        cursor = conn.cursor(as_dict=True)

        where_clauses = []
        params = []

        if date_from:
            where_clauses.append("created >= %s")
            params.append(date_from)

        if date_to:
            where_clauses.append("created <= %s")
            params.append(date_to)

        if search_text:
            where_clauses.append("(purchase_object LIKE %s OR customer LIKE %s)")
            search_param = f"%{search_text}%"
            params.extend([search_param, search_param])

        where_sql = ""
        if where_clauses:
            where_sql = "WHERE " + " AND ".join(where_clauses)

        # Получаем общее количество записей
        count_query = f"SELECT COUNT(*) as total FROM zakupki {where_sql}"
        cursor.execute(count_query, tuple(params))
        total = cursor.fetchone()['total']

        # Получаем записи с пагинацией
        query = f"""
            SELECT
                id,
                created as date_request,
                purchase_object,
                start_cost,
                customer,
                email,
                contact_number as phone,
                post_address as address
            FROM zakupki
            {where_sql}
            ORDER BY created DESC
            OFFSET %s ROWS
            FETCH NEXT %s ROWS ONLY
        """

        cursor.execute(query, tuple(params + [offset, limit]))
        results = cursor.fetchall()

        conn.close()

        return {
            'data': results,
            'total': total
        }

mssql = MSSQLConnection()

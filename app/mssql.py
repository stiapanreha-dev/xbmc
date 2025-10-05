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

    def get_zakupki(self, date_from=None, date_to=None, search_text=None, limit=100, offset=0, restrict_to_ids=None, count_all=False):
        """Получить закупки с фильтрацией

        Args:
            restrict_to_ids: Список ID для ограничения выборки (для неавторизированных пользователей)
            count_all: Если True, считать total без учета restrict_to_ids (для отображения реального кол-ва)
        """
        conn = self.get_connection()
        cursor = conn.cursor(as_dict=True)

        where_clauses = []
        params = []
        where_clauses_for_count = []
        params_for_count = []

        # Ограничение по ID (для неавторизированных пользователей)
        if restrict_to_ids is not None:
            if not restrict_to_ids:
                # Если список пустой, возвращаем пустой результат
                return {'data': [], 'total': 0}
            placeholders = ','.join(['%s'] * len(restrict_to_ids))
            where_clauses.append(f"z.id IN ({placeholders})")
            params.extend(restrict_to_ids)

        if date_from:
            where_clauses.append("z.created >= %s")
            params.append(date_from)
            where_clauses_for_count.append("z.created >= %s")
            params_for_count.append(date_from)

        if date_to:
            where_clauses.append("z.created <= %s")
            params.append(date_to)
            where_clauses_for_count.append("z.created <= %s")
            params_for_count.append(date_to)

        if search_text:
            # Поиск по zakupki + zakupki_specification
            search_clause = """(
                z.purchase_object LIKE %s
                OR z.customer LIKE %s
                OR EXISTS (
                    SELECT 1 FROM zakupki_specification zs
                    WHERE zs.id_zakupki = z.id
                    AND (zs.product LIKE %s OR zs.product_specification LIKE %s)
                )
            )"""
            where_clauses.append(search_clause)
            where_clauses_for_count.append(search_clause)
            search_param = f"%{search_text}%"
            params.extend([search_param, search_param, search_param, search_param])
            params_for_count.extend([search_param, search_param, search_param, search_param])

        where_sql = ""
        if where_clauses:
            where_sql = "WHERE " + " AND ".join(where_clauses)

        # Получаем общее количество записей
        if count_all and restrict_to_ids is not None:
            # Считаем без restrict_to_ids для отображения реального количества
            where_sql_for_count = ""
            if where_clauses_for_count:
                where_sql_for_count = "WHERE " + " AND ".join(where_clauses_for_count)
            count_query = f"SELECT COUNT(*) as total FROM zakupki z {where_sql_for_count}"
            cursor.execute(count_query, tuple(params_for_count))
        else:
            count_query = f"SELECT COUNT(*) as total FROM zakupki z {where_sql}"
            cursor.execute(count_query, tuple(params))
        total = cursor.fetchone()['total']

        # Получаем записи с пагинацией
        query = f"""
            SELECT
                z.id,
                z.created as date_request,
                z.purchase_object,
                isnull(z.start_cost_var, cast(z.start_cost as varchar(20))) as start_cost,
                z.customer,
                isnull(z.email, z.additional_contacts) as email,
                z.contact_number as phone,
                z.post_address as address,
                z.purchase_type
            FROM zakupki z
            {where_sql}
            ORDER BY z.id DESC
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

    def get_specifications(self, zakupki_id):
        """Получить спецификации для закупки"""
        conn = self.get_connection()
        cursor = conn.cursor(as_dict=True)

        query = """
            SELECT
                id,
                id_zakupki,
                product,
                product_specification,
                quantity,
                price_vat,
                terms_of_payment,
                delivery_time
            FROM zakupki_specification
            WHERE id_zakupki = %s
            ORDER BY id
        """

        cursor.execute(query, (zakupki_id,))
        results = cursor.fetchall()
        conn.close()

        return results

mssql = MSSQLConnection()

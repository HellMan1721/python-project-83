from dotenv import load_dotenv
import database

load_dotenv()


class URL:
    @staticmethod
    def all():
        """Все URL + дата И КОД последней проверки"""
        with database.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT 
                        u.id, 
                        u.name, 
                        u.created_at,
                        c.created_at as last_check,
                        c.status_code as last_status
                    FROM urls u 
                    LEFT JOIN (
                        SELECT url_id, 
                            created_at, 
                            status_code,
                            ROW_NUMBER() OVER (
                            PARTITION BY url_id ORDER BY created_at DESC
                            ) as rn
                        FROM url_checks
                    ) c ON u.id = c.url_id AND c.rn = 1
                    ORDER BY u.created_at DESC
                """)
                return cur.fetchall()

    @staticmethod
    def get(id):
        """Один URL по ID"""
        with database.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM urls WHERE id = %s", (id,))
                return cur.fetchone()

    @staticmethod
    def get_checks(url_id):
        """Все проверки для сайта"""
        with database.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT * FROM url_checks "
                    "WHERE url_id = %s ORDER BY created_at DESC",
                    (url_id,),
                )
                return cur.fetchall()


database.init_db()

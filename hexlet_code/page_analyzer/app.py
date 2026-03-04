from flask import Flask, render_template, flash, redirect, url_for, request
import os
import psycopg
from urllib.parse import urlparse
import validators
from dotenv import load_dotenv
from .urls import URL


load_dotenv()
app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY')


@app.route("/")
def index():
    return render_template('index.html')


@app.route("/urls", methods=['POST'])
def add_url():
    url = request.form.get('url', '').strip()
    
    # ВАЛИДАЦИЯ
    if not url:
        flash('URL не может быть пустым', 'danger')
        return render_template('index.html')
    
    normalized = URL.normalize(url)
    if not validators.url(normalized) or len(normalized) > 255:
        flash('Некорректный URL', 'danger')
        return render_template('index.html', url=url)
    
    # БАЗА ДАННЫХ
    try:
        with URL.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO urls (name) VALUES (%s) ON CONFLICT (name) DO NOTHING RETURNING id",
                    (normalized,)
                )
                result = cur.fetchone()
                
                if result:
                    url_id = result[0]
                else:
                    cur.execute("SELECT id FROM urls WHERE name = %s", (normalized,))
                    url_id = cur.fetchone()[0]
                
                conn.commit()
                
        flash('Страница успешно добавлена', 'success')
        return redirect(url_for('url_show', id=url_id))
        
    except Exception as e:
        print(f"DB Error: {e}")
        flash('Ошибка базы данных', 'danger')
        return render_template('index.html', url=url)


def get_checks(url_id):
    """Получить все проверки для URL"""
    with URL.get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT * FROM url_checks WHERE url_id = %s ORDER BY created_at DESC", 
                (url_id,)
            )
            return cur.fetchall()

def create_check(url_id):
    """Создать новую проверку (заглушка)"""
    with URL.get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO url_checks (url_id, status_code) VALUES (%s, 200) RETURNING id",
                (url_id,)
            )
            check_id = cur.fetchone()[0]
            conn.commit()
            return check_id


@app.route("/urls/<int:id>/checks", methods=['POST'])
def url_check(id):
    try:
        url = get_url(id)
        if not url:
            flash('Страница не найдена', 'danger')
            return redirect(url_for('urls_list'))
        
        create_check(id)
        flash('Страница успешно проверена', 'success')
    except Exception as e:
        print(f"Check error: {e}")
        flash('Произошла ошибка при проверке', 'danger')
    
    return redirect(url_for('url_show', id=id))


@app.route("/urls/<int:id>")
def url_show(id):
    try:
        url = get_url(id)
        checks = get_checks(id)
        if not url:
            flash('Страница не найдена', 'danger')
            return redirect(url_for('urls_list'))
        return render_template('url.html', url=url, checks=checks)
    except Exception:
        flash('Ошибка загрузки страницы', 'danger')
        return redirect(url_for('urls_list'))


@app.route("/urls", methods=['GET'])
def urls_list():
    try:
        with URL.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT u.*, c.created_at as last_check 
                    FROM urls u 
                    LEFT JOIN (
                        SELECT url_id, MAX(created_at) as created_at 
                        FROM url_checks 
                        GROUP BY url_id
                    ) c ON u.id = c.url_id 
                    ORDER BY u.created_at DESC
                """)
                urls = cur.fetchall()
        return render_template('urls.html', urls=urls)
    except Exception:
        flash('Ошибка загрузки списка', 'danger')
        return render_template('urls.html', urls=[])

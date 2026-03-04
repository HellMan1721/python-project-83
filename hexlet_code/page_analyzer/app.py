import os
from dotenv import load_dotenv
from flask import Flask, render_template, flash, redirect, url_for, request
from page_analyzer.urls import URL

load_dotenv()
app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY')

@app.route("/")
def index():
    return render_template('index.html')

@app.route("/urls", methods=['GET'])
def urls_list():
    urls = URL.all()
    return render_template('urls.html', urls=urls)

@app.route("/urls", methods=['POST'])
def add_url():
    url = request.form['url']
    try:
        url_id = URL.save(url)
        flash('Страница успешно добавлена', 'success')
        return redirect(url_for('url_show', id=url_id))
    except ValueError:
        flash('Некорректный URL', 'danger')
        return render_template('index.html', url=url)

@app.route("/urls/<int:id>")
def url_show(id):
    url = URL.get(id)
    if not url:
        flash('Страница не найдена', 'danger')
        return redirect(url_for('urls_list'))
    return render_template('url.html', url=url)

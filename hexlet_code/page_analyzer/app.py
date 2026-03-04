import os
from dotenv import load_dotenv
from flask import Flask, render_template, request

load_dotenv()
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret')  # секрет только из env!

@app.route("/")
def index():
    if request.method == "POST":
        url = request.form["url"]
        # Пока просто редирект (позже обработаем)
        return f"<h1>Анализ {url}</h1>"  # заглушка
    return render_template("index.html")

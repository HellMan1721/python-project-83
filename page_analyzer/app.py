from flask import Flask, render_template, flash, redirect, url_for, request
import os
from dotenv import load_dotenv
from .urls import URL, DuplicateUrlError, ValidationError

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "dev-secret-key")


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/urls", methods=["GET", "POST"])
def urls():
    if request.method == "POST":
        url = request.form.get("url", "").strip()

        if not url:
            flash("URL не может быть пустым", "danger")
            return render_template("index.html", url=url)

        try:
            url_id = URL.save(url)
            flash("Страница успешно добавлена", "success")
            return redirect(url_for("url_show", id=url_id))

        except DuplicateUrlError as e:
            flash(str(e), "danger")
        except ValidationError as e:
            flash(str(e), "danger")
        except Exception:
            flash("Ошибка базы данных", "danger")
            return render_template("index.html", url=url)

    urls = URL.all()
    return render_template("urls.html", urls=urls)


@app.route("/urls/<int:id>")
def url_show(id):
    url = URL.get(id)
    if not url:
        flash("Страница не найдена", "danger")
        return redirect(url_for("urls"))
    checks = URL.get_checks(id)
    return render_template("url.html", url=url, checks=checks)


@app.route("/urls/<int:id>/checks", methods=["POST"])
def url_check(id):
    try:
        URL.create_check(id)
        flash("Страница успешно проверена", "success")
    except Exception:
        flash("Произошла ошибка при проверке", "danger")
    return redirect(url_for("url_show", id=id))

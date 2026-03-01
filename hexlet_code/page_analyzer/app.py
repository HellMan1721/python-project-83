import os
from dotenv import load_dotenv
from flask import Flask

load_dotenv()
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret')  # секрет только из env!

@app.route('/')
def hello():
    return '<h1>Page Analyzer</h1>'

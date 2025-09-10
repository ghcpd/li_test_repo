from flask import Flask, jsonify, render_template, request, abort
import json
import os
import random

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(BASE_DIR, 'zodiacs.json')

with open(DATA_PATH, 'r', encoding='utf-8') as f:
    ZODIACS = json.load(f)

# Build a lookup map for quick name-based searches (case-insensitive)
ZODIAC_MAP = {z["name"].lower(): z for z in ZODIACS}


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/zodiacs')
def get_zodiacs():
    search = request.args.get('search', '').strip().lower()
    element = request.args.get('element', '').strip().lower()
    random_flag = request.args.get('random', '').strip().lower() in ['1', 'true', 'yes']

    items = ZODIACS

    if search:
        items = [z for z in items if search in z["name"].lower()]

    if element:
        items = [z for z in items if z["element"].lower() == element]

    if random_flag and items:
        items = [random.choice(items)]

    return jsonify(items)


@app.route('/zodiacs/<name>')
def get_zodiac(name):
    key = name.strip().lower()
    zodiac = ZODIAC_MAP.get(key)
    if not zodiac:
        abort(404, description=f"Zodiac '{name}' not found")
    return jsonify(zodiac)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=False)

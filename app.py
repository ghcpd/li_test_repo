from flask import Flask, jsonify, render_template, send_from_directory, request
import json
import os
import random

app = Flask(__name__, static_folder='static', template_folder='templates')

DATA_PATH = os.path.join(os.path.dirname(__file__), 'data', 'zodiacs.json')
with open(DATA_PATH, 'r', encoding='utf-8') as f:
    ZODIACS = json.load(f)

# Helpers
NAME_MAP = {z['name'].lower(): z for z in ZODIACS}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/zodiacs')
def list_zodiacs():
    q = request.args.get('q', '').strip().lower()
    element = request.args.get('element', '').strip().lower()
    results = ZODIACS
    if q:
        results = [z for z in results if q in z['name'].lower()]
    if element:
        results = [z for z in results if z['element'].lower() == element]
    return jsonify(results)

@app.route('/zodiacs/<name>')
def get_zodiac(name: str):
    z = NAME_MAP.get(name.strip().lower())
    if not z:
        return jsonify({'error': 'Zodiac not found'}), 404
    return jsonify(z)

@app.route('/zodiacs/random')
def random_zodiac():
    return jsonify(random.choice(ZODIACS))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

from flask import Flask, render_template, jsonify, request
import json
import random
import os

app = Flask(__name__)

# Load zodiac data
def load_zodiac_data():
    with open('zodiac_data.json', 'r', encoding='utf-8') as f:
        return json.load(f)

ZODIAC_DATA = load_zodiac_data()

@app.route('/')
def index():
    """Render the main page"""
    return render_template('index.html')

@app.route('/api/zodiacs', methods=['GET'])
def get_all_zodiacs():
    """Get all zodiac signs, optionally filtered by element"""
    element = request.args.get('element', '').lower()
    
    if element:
        filtered = [z for z in ZODIAC_DATA if z['element'].lower() == element]
        return jsonify(filtered)
    
    return jsonify(ZODIAC_DATA)

@app.route('/api/zodiacs/<string:name>', methods=['GET'])
def get_zodiac_by_name(name):
    """Get a specific zodiac sign by name"""
    name_lower = name.lower()
    
    for zodiac in ZODIAC_DATA:
        if zodiac['name'].lower() == name_lower:
            return jsonify(zodiac)
    
    return jsonify({'error': 'Zodiac sign not found'}), 404

@app.route('/api/zodiacs/random/get', methods=['GET'])
def get_random_zodiac():
    """Get a random zodiac sign"""
    zodiac = random.choice(ZODIAC_DATA)
    return jsonify(zodiac)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)

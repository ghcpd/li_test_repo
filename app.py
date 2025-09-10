from flask import Flask, render_template, jsonify, request
import json
import random
import os

app = Flask(__name__)

# Load zodiac data
def load_zodiac_data():
    with open('zodiac_data.json', 'r') as f:
        return json.load(f)

zodiac_data = load_zodiac_data()

@app.route('/')
def index():
    """Main page displaying all zodiac signs"""
    return render_template('index.html')

@app.route('/zodiacs')
def get_all_zodiacs():
    """API endpoint to get all zodiac signs"""
    element_filter = request.args.get('element', '').lower()
    search_query = request.args.get('search', '').lower()
    
    zodiacs = zodiac_data['zodiacs']
    
    # Filter by element if specified
    if element_filter:
        zodiacs = [z for z in zodiacs if z['element'].lower() == element_filter]
    
    # Filter by search query if specified
    if search_query:
        zodiacs = [z for z in zodiacs if search_query in z['name'].lower()]
    
    return jsonify({'zodiacs': zodiacs})

@app.route('/zodiacs/<name>')
def get_zodiac_by_name(name):
    """API endpoint to get a specific zodiac sign by name"""
    name_lower = name.lower()
    
    for zodiac in zodiac_data['zodiacs']:
        if zodiac['name'].lower() == name_lower:
            return jsonify(zodiac)
    
    return jsonify({'error': 'Zodiac sign not found'}), 404

@app.route('/zodiacs/random')
def get_random_zodiac():
    """API endpoint to get a random zodiac sign"""
    random_zodiac = random.choice(zodiac_data['zodiacs'])
    return jsonify(random_zodiac)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
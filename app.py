import os
from flask import Flask, render_template, jsonify
import json

app = Flask(__name__)

# Determine the absolute path to the competency_data.json file
base_dir = os.path.abspath(os.path.dirname(__file__))
competency_data_path = os.path.join(base_dir, 'static', 'competency_data.json')

# Load competency data
try:
    with open(competency_data_path, 'r') as file:
        competency_data = json.load(file)
except FileNotFoundError:
    # Fallback location - some hosting providers have different path structures
    alt_path = os.path.join(base_dir, 'competency_data.json')
    with open(alt_path, 'r') as file:
        competency_data = json.load(file)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/competencies', methods=['GET'])
def get_competencies():
    return jsonify(competency_data)

# Add additional routes as needed for your application

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)

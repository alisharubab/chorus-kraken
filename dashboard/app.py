import os
import json
import glob
from flask import Flask, jsonify, render_template
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
ARTIFACTS_DIR = os.path.join(PROJECT_ROOT, 'artifacts')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/state')
def get_state():
    decision_files = glob.glob(os.path.join(ARTIFACTS_DIR, 'decision_*.json'))
    if not decision_files:
        return jsonify({"error": "No decisions found"}), 404
        
    latest_decision = max(decision_files, key=os.path.getmtime)
    try:
        with open(latest_decision, 'r') as f:
            data = json.load(f)
            return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/contracts')
def get_contracts():
    contracts_file = os.path.join(PROJECT_ROOT, 'contract_addresses.json')
    try:
        with open(contracts_file, 'r') as f:
            data = json.load(f)
            return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=5000)

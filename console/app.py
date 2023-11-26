import requests
import json

from flask import Flask
from flask import render_template
from flask_cors import CORS
from flask import jsonify

LEARNING_URL_PREFIX = 'http://localhost:8080/learning'

app = Flask(__name__)
CORS(app)

@app.route('/')
def index():
    return render_template('index.html', content = 'Index')

@app.route('/topology')
def topology():
    return render_template('index.html', content = 'Topology')

@app.route('/statistics')
def statistics():
    return render_template('index.html', content = 'Statistics')

@app.route('/learning')
def learning():
    response = requests.get(LEARNING_URL_PREFIX + '/hosts')
    entity = response.json()
    return render_template('index.html', content = 'Learning', entity = entity)

@app.route('/learning/host/<name>')
def learningByName(name: str):
    response = requests.get(LEARNING_URL_PREFIX + '/host/' + name)
    entity = response.json()
    return render_template('index.html', content = 'LearningHost', entity = entity)

@app.route('/learning/add-host')
def learningAddHost():
    return render_template('index.html', content = 'LearningAddHost')
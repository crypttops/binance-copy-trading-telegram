from flask import Flask,jsonify, request, abort
from config import DevelopmentConfig, ProductionConfig
from flask_migrate import Migrate
from db import db
import logging
import json
import requests
from backend.models import BotConfigsModel
app = Flask(__name__)
app.config.from_object(ProductionConfig)
db.init_app(app)

migrate = Migrate(app, db)

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)




if __name__ == '__main__':
    # socketio.run(app, host='0.0.0.0', port=85)
    app.run(host='0.0.0.0', port=5000)
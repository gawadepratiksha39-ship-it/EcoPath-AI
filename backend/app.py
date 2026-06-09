"""
app.py — EcoPath AI Flask application entry point.
"""

import logging
import os

from flask import Flask, jsonify
from flask_cors import CORS

from models.database import init_db
from routes.auth import auth_bp
from routes.ai import ai_bp
from routes.routes import routes_bp
from routes.carbon import carbon_bp

logging.basicConfig(level=logging.INFO)

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("JWT_SECRET", "ecopath-dev-secret-change-in-production")

CORS(app, origins=["http://localhost:5173", "http://127.0.0.1:5173"])

app.register_blueprint(auth_bp)
app.register_blueprint(ai_bp)
app.register_blueprint(routes_bp)
app.register_blueprint(carbon_bp)


@app.route("/api/test", methods=["GET"])
def test():
    return jsonify({
        "status": "ok",
        "message": "EcoPath AI backend is running",
        "version": "0.2.0",
    })


if __name__ == "__main__":
    init_db()
    app.run(debug=True, port=5000)

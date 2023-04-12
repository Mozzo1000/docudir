from flask import Flask, url_for
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from api.models import db, ma
from api.config import DevConfig, ProdConfig
import os
from api.routes.auth import auth_endpoint
from api.routes.site import site_endpoint
from flasgger import Swagger

app = Flask(__name__)
CORS(app)
if os.environ.get("FLASK_DEBUG") == "1":
    app.config.from_object(DevConfig)
else:
    app.config.from_object(ProdConfig)
db.init_app(app)
ma.init_app(app)
migrate = Migrate(app, db)
jwt = JWTManager(app)

template = {
    "swagger": "2.0",
    "info": {
        "title": "docudir API Docs",
        "version": "1.0"
    },
    "basePath": "/",  # base bash for blueprint registration
    "schemes": [
        "http",
        "https"
    ],
    "securityDefinitions": {
        "Bearer": {
            "type": "apiKey",
            "name": "Authorization",
            "in": "header",
            "description": "JWT Authorization header using the Bearer scheme. Example: \"Authorization: Bearer {token}\""
        }
    },
    "security": [
        {
            "Bearer": []
        }
    ]
}

swagger = Swagger(app, template=template)

app.register_blueprint(auth_endpoint)
app.register_blueprint(site_endpoint)

@app.route("/")
def index():
    return {
        "name": "docudir-api",
        "version": "0.1.0"
    }
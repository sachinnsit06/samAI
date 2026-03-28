from flask import Flask
from flask_cors import CORS

from routes.api import api_bp
from routes.web import web_bp


def create_app():
    app = Flask(__name__)
    CORS(app)
    app.register_blueprint(web_bp)
    app.register_blueprint(api_bp)
    return app


app = create_app()


if __name__ == "__main__":
    print("Starting samAI Server...")
    print("\nPress Ctrl+C to stop the server")
    app.run(host="0.0.0.0", port=5000, debug=True)

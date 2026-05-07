import os

from dotenv import load_dotenv
from flask import Flask
from flask_cors import CORS

try:
    from .api import api
    from .init_sqlite import init_database
except ImportError:
    from api import api
    from init_sqlite import init_database

load_dotenv()

app = Flask(__name__)
CORS(app, resources={"*": {"origins": "*"}})
app.register_blueprint(api, url_prefix='/api')

try:
    init_database()
except Exception as e:
    print(f"SQLite initialization failed: {e}")


if __name__ == '__main__':
    host = os.getenv('HOST', '0.0.0.0')
    port = int(os.getenv('PORT', '5000'))
    debug = os.getenv('FLASK_DEBUG', '1') in ('1', 'true', 'True', 'yes', 'YES')
    app.run(debug=debug, host=host, port=port)

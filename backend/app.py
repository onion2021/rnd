import os

from dotenv import load_dotenv
from flask import Flask
from flask_cors import CORS
from api import api

load_dotenv()

app = Flask(__name__)
CORS(app, resources={"*": {"origins": "*"}})

app.register_blueprint(api, url_prefix='/api')

if __name__ == '__main__':
    # 启动时确保 SQLite 数据库/表已存在
    try:
        from init_sqlite import init_database
        init_database()
    except Exception as e:
        # 不要阻止服务启动；后续接口会因为表不存在而报错
        print(f"SQLite初始化失败: {e}")

    host = os.getenv('HOST', '0.0.0.0')
    port = int(os.getenv('PORT', '5000'))
    debug = os.getenv('FLASK_DEBUG', '1') in ('1', 'true', 'True', 'yes', 'YES')

    app.run(debug=debug, host=host, port=port)
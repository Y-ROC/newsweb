from flask import Flask
from flask_migrate import Migrate
from flask_session import Session
from flask_sqlalchemy import SQLAlchemy
from redis import StrictRedis

from config import config_dict
from info.modules.home import home_blu


# 创建应用 工厂函数
def create_app(config_type):
    # 根据类型取出配置类
    config_class = config_dict[config_type]
    app = Flask(__name__)
    # 从对象加载配置信息
    app.config.from_object(config_class)
    # 创建MySQL数据库连接
    db = SQLAlchemy(app)
    # 创建redis数据库连接
    sr = StrictRedis(host=config_class.REDIS_HOST, port=config_class.REDIS_PORT)
    # 创建session存储对象
    Session(app)
    # 创建迁移器
    Migrate(app, db)
    #3.注册蓝图
    app.register_blueprint(home_blu)
    return app

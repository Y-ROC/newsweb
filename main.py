from datetime import timedelta

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from redis import StrictRedis
from flask_session import Session
from flask_script import Manager
from flask_migrate import Migrate, MigrateCommand


class Config(object):
    DEBUGE = True
    # 设置数据库连接地址
    SQLALCHEMY_DATABASE_URI = 'mysql://root:mysql@localhost:3306/newsinfo'
    # 是否追踪数据库变化
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    REDIS_HOST = 'localhost'
    REDIS_PORT = 6379
    SESSION_TYPE = 'redis'
    # 设置存储session的redis连接对象
    SESSION_REDIS = StrictRedis(host=REDIS_HOST, port=REDIS_PORT)
    # 设置给sessionid加密钥
    SESSION_USE_SIGNER = True
    # 应用密钥
    SECRET_KEY = 'ySB+rb2WNKamAqBU4lXU0zQdf2hz+XJ80esKpQ2krNx04Hhl8n3orTg5jwhadvti'
    # 设置session的过期时间
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)


app = Flask(__name__)
# 从对象加载配置信息
app.config.from_object(Config)
# 创建MySQL数据库连接
db = SQLAlchemy(app)
# 创建redis数据库连接
sr = StrictRedis(host=Config.REDIS_HOST, port=Config.REDIS_PORT)
# 创建session存储对象
Session(app)
# 创建管理器
mgr = Manager(app)
# 创建迁移器
Migrate(app, db)
# 添加迁移命令
mgr.add_command('mc', MigrateCommand)


@app.route('/')
def index():
    return "index"


if __name__ == '__main__':
    mgr.run()

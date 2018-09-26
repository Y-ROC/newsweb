import logging
from datetime import timedelta
from redis import StrictRedis


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


# 开发环境配置
class DevelopmentConfig(Config):
    DEBUGE = True
    LOG_LEVEL = logging.DEBUG


# 生产环境配置
class ProduceConfig(Config):
    DEBUGE = False
    LOG_LEVEL = logging.ERROR


config_dict = {
    'dev': DevelopmentConfig,
    'pro': ProduceConfig
}

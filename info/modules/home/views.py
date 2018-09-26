from info import sr
from info.modules.home import home_blu


# 2.使用蓝图注册路由
@home_blu.route('/')
def index():
    sr.set('age', 18)
    return "index"

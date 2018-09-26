from info import sr
from info.modules.home import home_blu
from flask import render_template


# 2.使用蓝图注册路由
@home_blu.route('/')
def index():
    return render_template('index.html')

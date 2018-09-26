from info import sr
from info.modules.home import home_blu
from flask import render_template, current_app


# 2.使用蓝图注册路由
@home_blu.route('/')
def index():
    return render_template('index.html')


# 设置网站小图标
@home_blu.route('/favicon.ico')
def favicon():
    return current_app.send_static_file('news/favicon.ico')

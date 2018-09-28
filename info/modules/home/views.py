from info import sr
from info.models import User
from info.modules.home import home_blu
from flask import render_template, current_app, session


# 2.使用蓝图注册路由
@home_blu.route('/')
def index():
    user_id = session.get('user_id')
    user = None
    if user_id:
        try:
            user = User.query.get(user_id)
        except BaseException as e:
            current_app.logger.error(e)
    user = user.to_dict() if user else None
    return render_template('index.html', user=user)


# 设置网站小图标
@home_blu.route('/favicon.ico')
def favicon():
    return current_app.send_static_file('news/favicon.ico')

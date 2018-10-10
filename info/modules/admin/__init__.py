from flask import Blueprint

# 1.创建蓝图
admin_blu = Blueprint('admin', __name__, url_prefix='/admin')


@admin_blu.before_request
def check_superuser():  # 给蓝图设置请求钩子(只会拦截该蓝图注册的路由)
    # 判断管理员是否登录,如果没登录,重定向到后台首页
    is_admin = session.get('is_admin')
    if not is_admin and not request.url.endswith('admin/login'):
        return redirect(url_for('home.index'))


# 4.关联视图函数
from .views import *

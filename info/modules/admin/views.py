from info.models import User
from info.modules.admin import admin_blu
from flask import render_template, request, redirect, url_for, session


# 后台登录
@admin_blu.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == 'GET':
        # 取出session中的数据如果已登录,直接重定向到后台首页
        user_id = session.get('user_id')
        is_admin = session.get('is_admin')
        if user_id and is_admin:
            return redirect(url_for('admin.index'))
        return render_template("admin/login.html")
    # POST处理
    username = request.form.get('username')
    password = request.form.get('password')
    if not all([username, password]):
        return render_template('admin/login.html', errmsg="参数不完整")
    # 取出用户模型
    try:
        user = User.query.filter(User.mobile == username, User.is_admin == True).first()
    except BaseException as e:
        return render_template('admin/login.html', errmsg="数据库操作错误")
    if not user:
        return render_template('admin/login.html', errmsg="该管理员不存在")
    # 校验密码
    if not user.check_password(password):
        return render_template('admin/login.html', errmsg="用户或密码错误")
    # 状态保持
    session['user_id'] = user.id
    session['is_admin'] = True
    return redirect(url_for("admin.index"))


# 后台首页
@admin_blu.route('/index')
def index():
    return render_template("admin/index.html")


# 退出
@admin_blu.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('is_admin', None)
    return redirect(url_for('home.index'))

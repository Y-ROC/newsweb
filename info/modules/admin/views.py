import time
from datetime import datetime, timedelta

from info import db
from info.comments import user_login_data, img_upload
from info.constants import ADMIN_USER_PAGE_MAX_COUNT, ADMIN_NEWS_PAGE_MAX_COUNT, QINIU_DOMIN_PREFIX
from info.models import User, News, Category
from info.modules.admin import admin_blu
from flask import render_template, request, redirect, url_for, session, current_app, abort, g, jsonify

# 后台登录
from info.utils.response_code import RET, error_map


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
@user_login_data
def index():
    user = g.user
    return render_template("admin/index.html", user=user)


# 退出
@admin_blu.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('is_admin', None)
    return redirect(url_for('home.index'))


# 用户统计
@admin_blu.route('/user_count')
def user_count():
    # 用户总数
    total_count = 0
    try:
        total_count = User.query.filter(User.is_admin == False).count()
    except BaseException as e:
        current_app.logger.error(e)
    # 月新增人数
    mon_count = 0
    # 获取当前的时间 年和月
    t = time.localtime()
    # 构建目标日期字符串
    date_mon_str = "%d-%02d-01" % (t.tm_year, t.tm_mon)
    date_mon = datetime.strptime(date_mon_str, '%Y-%m-%d')
    try:
        mon_count = User.query.filter(User.is_admin == False, User.create_time >= date_mon).count()
    except BaseException as e:
        current_app.logger.error(e)

    # 日新增人数
    day_count = 0
    # 构建目标日期字符串
    date_day_str = "%d-%02d-%02d" % (t.tm_year, t.tm_mon, t.tm_mday)
    date_day = datetime.strptime(date_day_str, '%Y-%m-%d')
    try:
        day_count = User.query.filter(User.is_admin == False, User.create_time >= date_day).count()
    except BaseException as e:
        current_app.logger.error(e)

    # 获取前三十天每日注册的人数(注册日期>=某日0点,<=次日0点)
    active_count = []
    active_time = []
    for i in range(30):
        begin_date = date_day - timedelta(days=i)
        end_date = date_day + timedelta(days=1 - i)
        try:
            one_day_count = User.query.filter(User.is_admin == False, User.create_time >= begin_date,
                                              User.create_time <= end_date).count()
            active_count.append(one_day_count)
            one_day_str = begin_date.strftime("%Y-%m-%d")
            active_time.append(one_day_str)
        except BaseException as e:
            current_app.logger.error(e)

    active_count.reverse()
    active_time.reverse()
    data = {
        "total_count": total_count,
        "mon_count": mon_count,
        "day_count": day_count,
        "active_count": active_count,
        "active_time": active_time
    }
    return render_template('admin/user_count.html', data=data)


# 显示用户列表
@admin_blu.route('/user_list')
def user_list():
    # 获取当前页码
    p = request.args.get("p", 1)
    try:
        p = int(p)
    except BaseException as e:
        current_app.logger.error(e)
        return abort(403)
    # 查询所有用户的信息 指定页码
    user_list = []
    cur_page = 1
    total_page = 1
    try:
        pn = User.query.filter(User.is_admin == False).paginate(p, ADMIN_USER_PAGE_MAX_COUNT)
        user_list = [user.to_admin_dict() for user in pn.items]
        cur_page = pn.page
        total_page = pn.pages
    except BaseException as e:
        current_app.logger.error(e)
    data = {
        "user_list": user_list,
        "cur_page": cur_page,
        "total_page": total_page
    }
    return render_template("admin/user_list.html", data=data)


# 显示新闻审核列表
@admin_blu.route('/news_review')
def news_review():
    # 获取当前页码
    p = request.args.get("p", 1)
    keyword = request.args.get('keyword')
    try:
        p = int(p)
    except BaseException as e:
        current_app.logger.error(e)
        return abort(403)
    # 判断如果设置了keyword,添加对应的过滤条件
    filter_list = []
    if keyword:
        filter_list.append(News.title.contains(keyword))
    # 查询所有新闻的信息 指定页码
    news_list = []
    cur_page = 1
    total_page = 1
    try:
        pn = News.query.filter(*filter_list).paginate(p, ADMIN_NEWS_PAGE_MAX_COUNT)
        news_list = [news.to_review_dict() for news in pn.items]
        cur_page = pn.page
        total_page = pn.pages
    except BaseException as e:
        current_app.logger.error(e)
    data = {
        "news_list": news_list,
        "cur_page": cur_page,
        "total_page": total_page
    }
    return render_template("admin/news_review.html", data=data)


# 显示新闻审核详情
@admin_blu.route('/news_review_detail/<int:news_id>')
def news_review_detail(news_id):
    # 根据新闻id取出新闻模型
    try:
        news = News.query.get(news_id)
    except BaseException as e:
        current_app.logger.error(e)
        return abort(404)
    return render_template("admin/news_review_detail.html", news=news.to_dict())


# 提交审核
@admin_blu.route('/news_review_action', methods=['POST'])
def news_review_action():
    # 获取参数
    news_id = request.json.get('news_id')
    action = request.json.get('action')
    reason = request.json.get('reason')
    # 校验参数
    if not all([news_id, action]):
        return jsonify(errno=RET.PARAMERR, errmsg=error_map[RET.PARAMERR])
    if action not in ['accept', 'reject']:
        return jsonify(errno=RET.PARAMERR, errmsg=error_map[RET.PARAMERR])
    try:
        news_id = int(news_id)
    except BaseException as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.PARAMERR, errmsg=error_map[RET.PARAMERR])
    # 取出新闻模型
    try:
        news = News.query.get(news_id)
    except BaseException as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg=error_map[RET.DBERR])
    if not news:
        return jsonify(errno=RET.PARAMERR, errmsg=error_map[RET.PARAMERR])
    # 根据action设置status
    if action == 'accept':
        news.status = 0
    else:
        news.status = -1
        if not reason:
            return jsonify(errno=RET.PARAMERR, errmsg=error_map[RET.PARAMERR])
        news.reason = reason
    return jsonify(errno=RET.OK, errmsg=error_map[RET.OK])


# 显示新闻编辑列表
@admin_blu.route('/news_edit')
def news_edit():
    # 获取当前页码
    p = request.args.get("p", 1)
    keyword = request.args.get('keyword')
    try:
        p = int(p)
    except BaseException as e:
        current_app.logger.error(e)
        return abort(403)
    # 判断如果设置了keyword,添加对应的过滤条件
    filter_list = []
    if keyword:
        filter_list.append(News.title.contains(keyword))
    # 查询所有新闻的信息 指定页码
    news_list = []
    cur_page = 1
    total_page = 1
    try:
        pn = News.query.filter(*filter_list).paginate(p, ADMIN_NEWS_PAGE_MAX_COUNT)
        news_list = [news.to_review_dict() for news in pn.items]
        cur_page = pn.page
        total_page = pn.pages
    except BaseException as e:
        current_app.logger.error(e)
    data = {
        "news_list": news_list,
        "cur_page": cur_page,
        "total_page": total_page
    }
    return render_template("admin/news_edit.html", data=data)


# 显示新闻编辑详情
@admin_blu.route('/news_edit_detail/<int:news_id>')
def news_edit_detail(news_id):
    # 根据新闻id取出新闻模型
    try:
        news = News.query.get(news_id)
    except BaseException as e:
        current_app.logger.error(e)
        return abort(404)
    # 将所有分类以及新闻对应的分类传入模板
    categories = []
    try:
        categories = Category.query.all()
    except BaseException as e:
        current_app.logger.error(e)
    category_list = []
    for category in categories:
        category_dict = category.to_dict()
        is_selected = False
        if category.id == news.category_id:
            is_selected = True
        category_dict['is_selected'] = is_selected
        category_list.append(category_dict)
    # 删除'最新'
    if len(category_list):
        category_list.pop(0)
    # 将数据传入模板渲染
    return render_template('admin/news_edit_detail.html', news=news.to_dict(), category_list=category_list)


# 提交编辑
@admin_blu.route('/news_edit_detail', methods=['POST'])
def news_edit_action():
    # 获取参数
    news_id = request.form.get("news_id")
    category_id = request.form.get("category_id")
    title = request.form.get("title")
    digest = request.form.get("digest")
    content = request.form.get("content")
    index_image = request.files.get("index_image")
    # 校验参数
    if not all([news_id, category_id, title, digest, content]):
        return jsonify(errno=RET.PARAMERR, errmsg=error_map[RET.PARAMERR])

    try:
        news_id = int(news_id)
        category_id = int(category_id)
    except BaseException as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.PARAMERR, errmsg=error_map[RET.PARAMERR])

    # 取出新闻模型
    try:
        news = News.query.get(news_id)
        category = Category.query.get(category_id)
    except BaseException as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg=error_map[RET.DBERR])

    if not news or not category:
        return jsonify(errno=RET.PARAMERR, errmsg=error_map[RET.PARAMERR])

    # 修改数据
    news.title = title
    news.digest = digest
    news.category_id = category_id
    news.content = content

    if index_image:
        try:
            img_bytes = index_image.read()
            file_name = img_upload(img_bytes)
            news.index_image_url = QINIU_DOMIN_PREFIX + file_name
        except BaseException as e:
            current_app.logger.error(e)
            return jsonify(errno=RET.PARAMERR, errmsg=error_map[RET.PARAMERR])

    # json返回
    return jsonify(errno=RET.OK, errmsg=error_map[RET.OK])


# 新增/修改新闻分类
@admin_blu.route('/news_type', methods=['GET', 'POST'])
def news_type():
    if request.method == "GET":  # 显示页面
        # 查询所有的分类, 传入模板
        categories = []
        try:
            categories = Category.query.filter(Category.id != 1).all()
        except BaseException as e:
            current_app.logger.error(e)

        return render_template("admin/news_type.html", categories=categories)

    # POST处理
    id = request.json.get("id")
    name = request.json.get("name")
    if not name:
        return jsonify(errno=RET.PARAMERR, errmsg=error_map[RET.PARAMERR])

    if id:  # 修改
        try:
            id = int(id)
        except BaseException as e:
            current_app.logger.error(e)
            return jsonify(errno=RET.PARAMERR, errmsg=error_map[RET.PARAMERR])

        try:
            category = Category.query.get(id)
        except BaseException as e:
            current_app.logger.error(e)
            return jsonify(errno=RET.DBERR, errmsg=error_map[RET.DBERR])

        if not category:
            return jsonify(errno=RET.PARAMERR, errmsg=error_map[RET.PARAMERR])

        category.name = name

    else:  # 新增
        new_category = Category()
        new_category.name = name
        db.session.add(new_category)

    return jsonify(errno=RET.OK, errmsg=error_map[RET.OK])

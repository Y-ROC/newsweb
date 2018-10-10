from info import db
from info.comments import user_login_data, img_upload
from info.constants import USER_COLLECTION_MAX_NEWS, QINIU_DOMIN_PREFIX
from info.models import tb_user_collection, Category, News
from info.modules.user import user_blu
from flask import render_template, g, redirect, abort, request, jsonify, current_app

# 显示个人中心
from info.utils.response_code import RET, error_map


@user_blu.route('/user_info')
@user_login_data
def user_info():
    # 判断用户是否登录
    user = g.user
    if not user:
        return redirect('/')
    return render_template('user.html', user=user.to_dict())


# 显示/修改基本资料
@user_blu.route('/base_info', methods=["POST", "GET"])
@user_login_data
def base_info():
    # 判断用户是否登录
    user = g.user
    if not user:
        return abort(403)
    if request.method == 'GET':
        return render_template('user_base_info.html', user=user.to_dict())
    # POST处理
    signature = request.json.get('signature')
    nick_name = request.json.get('nick_name')
    gender = request.json.get('gender')
    if not all([signature, nick_name, gender]):
        return jsonify(errno=RET.PARAMERR, errmsg=error_map[RET.PARAMERR])
    if gender not in ['MAN', 'WOMAN']:
        return jsonify(errno=RET.PARAMERR, errmsg=error_map[RET.PARAMERR])
    # 修改用户模型
    user.signature = signature
    user.nick_name = nick_name
    user.gender = gender
    return jsonify(errno=RET.OK, errmsg=error_map[RET.OK])


# 显示/修改头像
@user_blu.route('/pic_info', methods=["POST", "GET"])
@user_login_data
def pic_info():
    # 判断用户是否登录
    user = g.user
    if not user:
        return abort(403)
    if request.method == 'GET':
        return render_template('user_pic_info.html', user=user.to_dict())
    # POST处理
    try:
        img_bytes = request.files.get('avatar').read()
        # 将文件上传给文件服务器
        try:
            file_name = img_upload(img_bytes)
            # 记录头像的URL
            user.avatar_url = file_name
        except BaseException as e:
            current_app.logger.error(e)
            return jsonify(errno=RET.THIRDERR, errmsg=error_map[RET.THIRDERR])
    except BaseException as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.PARAMERR, errmsg=error_map[RET.PARAMERR])
    return jsonify(errno=RET.OK, errmsg=error_map[RET.OK], data=user.to_dict())


# 密码修改
@user_blu.route('/pass_info', methods=["POST", "GET"])
@user_login_data
def pass_info():
    # 判断用户是否登录
    user = g.user
    if not user:
        return abort(403)
    if request.method == 'GET':
        return render_template('user_pass_info.html')
    # POST处理
    old_password = request.json.get('old_password')
    new_password = request.json.get('new_password')
    if not all([old_password, new_password]):
        return jsonify(errno=RET.PARAMERR, errmsg=error_map[RET.PARAMERR])
    # 校验密码
    if not user.check_password(old_password):
        return jsonify(errno=RET.PARAMERR, errmsg="密码错误")
    # 校验正确,修改密码
    user.password = new_password
    return jsonify(errno=RET.OK, errmsg=error_map[RET.OK])


# 显示我的收藏
@user_blu.route('/collection')
@user_login_data
def collection():
    # 判断用户是否登录
    user = g.user
    if not user:
        return abort(403)
    # 获取当前页码
    p = request.args.get('p', 1)
    try:
        p = int(p)
    except BaseException as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.PARAMERR, errmsg=error_map[RET.PARAMERR])
    # 查询当前用户收藏的所有新闻
    news_list = []
    cur_page = 1
    total_page = 1
    try:
        pn = user.collection_news.order_by(tb_user_collection.c.create_time.desc()).paginate(p,
                                                                                             USER_COLLECTION_MAX_NEWS)
        news_list = [news.to_basic_dict() for news in pn.items]
        cur_page = pn.page
        total_page = pn.pages
    except BaseException as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg=error_map[RET.DBERR])
    data = {
        "news_list": news_list,
        "cur_page": cur_page,
        "total_page": total_page
    }
    return render_template("user_collection.html", data=data)


# 显示界面/发布新闻
@user_blu.route('/news_release', methods=['GET', 'POST'])
@user_login_data
def news_release():
    # 判断用户是否登录
    user = g.user
    if not user:
        return abort(403)
    if request.method == 'GET':
        categories = []
        try:
            categories = Category.query.all()
        except BaseException as e:
            current_app.logger.error(e)
            return jsonify(errno=RET.DBERR, errmsg=error_map[RET.DBERR])
        if len(categories):
            categories.pop(0)
        return render_template("user_news_release.html", categories=categories)
    # POST处理
    title = request.form.get('title')
    category_id = request.form.get('category_id')
    digest = request.form.get('digest')
    content = request.form.get('content')
    if not all([title, category_id, digest, content]):
        return jsonify(errno=RET.PARAMERR, errmsg=error_map[RET.PARAMERR])
    try:
        category_id = int(category_id)
    except BaseException as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.PARAMERR, errmsg=error_map[RET.PARAMERR])
    # 生成一个新的新闻模型
    news = News()
    news.title = title
    news.content = content
    news.digest = digest
    news.category_id = category_id
    news.source = '个人发布'
    news.user_id = user.id
    news.status = 1
    try:
        img_bytes = request.files.get('index_image').read()
        file_name = img_upload(img_bytes)
        news.index_image_url = QINIU_DOMIN_PREFIX + file_name
    except BaseException as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.PARAMERR, errmsg=error_map[RET.PARAMERR])
    # 添加到数据库中
    db.session.add(news)
    return jsonify(errno=RET.OK, errmsg=error_map[RET.OK])


# 显示我的发布
@user_blu.route('/news_list')
@user_login_data
def news_list():
    # 判断用户是否登录
    user = g.user
    if not user:
        return abort(403)
    # 获取当前页码
    p = request.args.get('p', 1)
    try:
        p = int(p)
    except BaseException as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.PARAMERR, errmsg=error_map[RET.PARAMERR])
    # 查询当前用户收藏的所有新闻
    news_list = []
    cur_page = 1
    total_page = 1
    try:
        pn = user.news_list.order_by(News.create_time.desc()).paginate(p,
                                                                       USER_COLLECTION_MAX_NEWS)
        news_list = [news.to_review_dict() for news in pn.items]
        cur_page = pn.page
        total_page = pn.pages
    except BaseException as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg=error_map[RET.DBERR])
    data = {
        "news_list": news_list,
        "cur_page": cur_page,
        "total_page": total_page
    }
    return render_template("user_news_list.html", data=data)

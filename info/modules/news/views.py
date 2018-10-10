from flask import current_app, abort, render_template, request, jsonify, g
from info import db
from info.comments import user_login_data
from info.constants import CLICK_RANK_MAX_NEWS
from info.models import News, Comment
from info.modules.news import news_blu
from info.utils.response_code import RET, error_map


# 详情页面
@news_blu.route('/<int:news_id>')
@user_login_data
def news_detail(news_id):
    # 根据news_id查询新闻信息
    try:
        news = News.query.get(news_id)
    except BaseException as e:
        current_app.logger.error(e)
        return abort(404)
    # 点击量加1
    news.clicks += 1
    # 查询点击量排行前十的新闻
    news_list = []
    try:
        news_list = News.query.order_by(News.clicks.desc()).limit(CLICK_RANK_MAX_NEWS).all()
    except BaseException as e:
        current_app.logger.error(e)
    news_list = [news.to_basic_dict() for news in news_list]

    user = g.user
    is_collect = False
    if user:
        if news in user.collection_news:
            is_collect = True
    # 查询该新闻的所有评论,进行模板渲染
    try:
        comments = news.comments.order_by(Comment.create_time.desc()).all()
    except BaseException as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg=error_map[RET.DBERR])

    comment_list = []
    for comment in comments:
        comment_dict = comment.to_dict()
        is_like = False
        if user:
            if comment in user.like_comments:
                is_like = True
        comment_dict["is_like"] = is_like
        comment_list.append(comment_dict)
    user = user.to_dict() if user else None
    # 将数据传入模板进行模板渲染
    return render_template('news/detail.html', user=user, news=news.to_dict(), news_list=news_list, is_collect=is_collect,
                           comments=comment_list)


# 收藏
@news_blu.route('/news_collect', methods=['POST'])
@user_login_data
def news_collect():
    # 判断用户是否登录
    user = g.user
    if not user:
        return jsonify(errno=RET.SESSIONERR, errmsg=error_map[RET.SESSIONERR])
    # 获取参数
    news_id = request.json.get('news_id')
    action = request.json.get('action')
    # 校验参数
    if not all([news_id, action]):
        return jsonify(errno=RET.PARAMERR, errmsg=error_map[RET.PARAMERR])
    try:
        news_id = int(news_id)
    except BaseException as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.PARAMERR, errmsg=error_map[RET.PARAMERR])
    # 判断该新闻是否存在
    try:
        news = News.query.get(news_id)
    except BaseException as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg=error_map[RET.DBERR])
    if not news:
        return jsonify(errno=RET.PARAMERR, errmsg=error_map[RET.PARAMERR])
    if action not in ["collect", "cancel_collect"]:
        return jsonify(errno=RET.PARAMERR, errmsg=error_map[RET.PARAMERR])
    # 根据action执行收藏和取消收藏操作
    if action == 'collect':
        # 让user和news建立关系
        user.collection_news.append(news)
    else:
        user.collection_news.remove(news)
    # 返回json结果
    return jsonify(errno=RET.OK, errmsg=error_map[RET.OK])


# 评论/回复
@news_blu.route('/news_comment', methods=['POST'])
@user_login_data
def news_comment():
    # 判断用户是否登录
    user = g.user
    if not user:
        return jsonify(errno=RET.SESSIONERR, errmsg=error_map[RET.SESSIONERR])
    # 获取参数
    comment_content = request.json.get('comment')
    news_id = request.json.get('news_id')
    parent_id = request.json.get('parent_id')
    # 校验参数
    if not all([comment_content, news_id]):
        return jsonify(errno=RET.PARAMERR, errmsg=error_map[RET.PARAMERR])
    try:
        news_id = int(news_id)
    except BaseException as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.PARAMERR, errmsg=error_map[RET.PARAMERR])
    # 判断该新闻是否存在
    try:
        news = News.query.get(news_id)
    except BaseException as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg=error_map[RET.DBERR])
    if not news:
        return jsonify(errno=RET.PARAMERR, errmsg=error_map[RET.PARAMERR])
    # 生成一个评论数据添加到数据库中
    comment = Comment()
    comment.content = comment_content
    comment.news_id = news_id
    comment.user_id = user.id
    if parent_id:
        try:
            parent_id = int(parent_id)
            comment.parent_id = parent_id
        except BaseException as e:
            current_app.logger.error(e)
            return jsonify(errno=RET.PARAMERR, errmsg=error_map[RET.PARAMERR])
    try:
        db.session.add(comment)
        db.session.commit()  # 此处必须手动提交,否则不生成评论id,前端获取不到评论id
    except BaseException as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg=error_map[RET.DBERR])
    # 返回json结果
    return jsonify(errno=RET.OK, errmsg=error_map[RET.OK], data=comment.to_dict())


# 点赞
@news_blu.route('/comment_like', methods=['POST'])
@user_login_data
def comment_like():
    # 判断用户是否登录
    user = g.user
    if not user:
        return jsonify(errno=RET.SESSIONERR, errmsg=error_map[RET.SESSIONERR])
    # 获取参数
    comment_id = request.json.get('comment_id')
    action = request.json.get('action')
    # 校验参数
    if not all([comment_id, action]):
        return jsonify(errno=RET.PARAMERR, errmsg=error_map[RET.PARAMERR])
    try:
        comment_id = int(comment_id)
    except BaseException as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.PARAMERR, errmsg=error_map[RET.PARAMERR])
    # 判断该评论是否存在
    try:
        comment = Comment.query.get(comment_id)
    except BaseException as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg=error_map[RET.DBERR])
    if not comment:
        return jsonify(errno=RET.PARAMERR, errmsg=error_map[RET.PARAMERR])
    if action not in ["add", "remove"]:
        return jsonify(errno=RET.PARAMERR, errmsg=error_map[RET.PARAMERR])
    # 根据action执行点赞和取消点赞操作
    if action == 'add':
        # 让user和comment建立关系
        user.like_comments.append(comment)
        comment.like_count += 1
    else:
        user.like_comments.remove(comment)
        comment.like_count -= 1
    # 返回json结果
    return jsonify(errno=RET.OK, errmsg=error_map[RET.OK])

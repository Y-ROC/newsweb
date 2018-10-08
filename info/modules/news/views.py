from flask import current_app, abort, render_template, session, request, jsonify, g
from info.comments import user_login_data
from info.constants import CLICK_RANK_MAX_NEWS
from info.models import News
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
    user = user.to_dict() if user else None
    # 将数据传入模板进行模板渲染
    return render_template('detail.html', user=user, news=news.to_dict(), news_list=news_list, is_collect=is_collect)


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

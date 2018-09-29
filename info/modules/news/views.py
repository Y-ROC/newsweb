from flask import current_app, abort, render_template, session

from info.constants import CLICK_RANK_MAX_NEWS
from info.models import News, User
from info.modules.news import news_blu


# 详情页面
@news_blu.route('/<int:news_id>')
def news_detail(news_id):
    # 登录信息
    user_id = session.get('user_id')
    user = None
    if user_id:
        try:
            user = User.query.get(user_id)
        except BaseException as e:
            current_app.logger.error(e)
    user = user.to_dict() if user else None
    # 根据news_id查询新闻信息
    try:
        news = News.query.get(news_id)
    except BaseException as e:
        current_app.logger.error(e)
        return abort(404)
    # 查询点击量排行前十的新闻
    news_list = []
    try:
        news_list = News.query.order_by(News.clicks.desc()).limit(CLICK_RANK_MAX_NEWS).all()
    except BaseException as e:
        current_app.logger.error(e)
    news_list = [news.to_basic_dict() for news in news_list]
    # 将数据传入模板进行模板渲染
    return render_template('detail.html', user=user, news=news.to_dict(), news_list=news_list)

from info import sr
from info.constants import CLICK_RANK_MAX_NEWS
from info.models import User, News, Category
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
    # 查询点击量排行前十的新闻
    news_list = []
    try:
        news_list = News.query.order_by(News.clicks.desc()).limit(CLICK_RANK_MAX_NEWS).all()
    except BaseException as e:
        current_app.logger.error(e)
    news_list = [news.to_basic_dict() for news in news_list]
    #查询所有分类信息
    categories=[]
    try:
        categories= Category.query.all()
    except BaseException as e:
        current_app.logger.error(e)
    return render_template('index.html', user=user, news_list=news_list,categories=categories)


# 设置网站小图标
@home_blu.route('/favicon.ico')
def favicon():
    return current_app.send_static_file('news/favicon.ico')

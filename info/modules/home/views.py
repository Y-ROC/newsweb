from info.constants import CLICK_RANK_MAX_NEWS, HOME_PAGE_MAX_NEWS
from info.models import User, News, Category
from info.modules.home import home_blu
from flask import render_template, current_app, session, request, jsonify
from info.utils.response_code import RET, error_map


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
    # 查询所有分类信息
    categories = []
    try:
        categories = Category.query.all()
    except BaseException as e:
        current_app.logger.error(e)
    return render_template('index.html', user=user, news_list=news_list, categories=categories)


# 设置网站小图标
@home_blu.route('/favicon.ico')
def favicon():
    return current_app.send_static_file('news/favicon.ico')


# 获取新闻列表
@home_blu.route('/get_news_list')
def get_news_list():
    # 获取参数
    cid = request.args.get('cid')  # 分类id
    cur_page = request.args.get('cur_page')  # 当前页码
    per_count = request.args.get('per_count', HOME_PAGE_MAX_NEWS)  # 每页条数
    # 校验参数
    if not all([cid, cur_page, per_count]):
        return jsonify(errno=RET.PARAMERR, errmsg=error_map[RET.PARAMERR])
    # 格式转换
    try:
        cid = int(cid)
        cur_page = int(cur_page)
        per_count = int(per_count)
    except BaseException as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.PARAMERR, errmsg=error_map[RET.PARAMERR])
    # 判断分类id是否等于1  '最新'是所有新闻一起排列,不包括具体新闻
    filter_list = []
    if cid != 1:
        filter_list.append(News.category_id == cid)
    # 根据参数查询目标新闻
    try:
        pn = News.query.filter(*filter_list).order_by(News.create_time.desc()).paginate(cur_page, per_count)
    except BaseException as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg=error_map[RET.DBERR])
    data = {
        "news_list": [news.to_basic_dict() for news in pn.items],
        "total_page": pn.pages
    }
    # 将新闻包装为json并返回
    return jsonify(errno=RET.OK, errmsg=error_map[RET.OK], data=data)

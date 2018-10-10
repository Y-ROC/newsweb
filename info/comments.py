import functools

from flask import session, current_app, g

from info.models import User


def func_index_convert(index):
    index_dict = {1: 'first', 2: 'second', 3: 'third'}
    return index_dict.get(index, '')


# 装饰器来封装登录信息的查询
def user_login_data(f):
    @functools.wraps(f)  # 该装饰器可以让闭包函数使用指定函数的信息
    def wrapper(*args, **kwargs):
        user_id = session.get('user_id')
        user = None
        if user_id:
            try:
                user = User.query.get(user_id)
            except BaseException as e:
                current_app.logger.error(e)
        g.user = user
        return f(*args, **kwargs)

    return wrapper


access_key = "kJ8wVO7lmFGsdvtI5M7eQDEJ1eT3Vrygb4SmR00E"
secret_key = "rGwHyAvnlLK7rU4htRpNYzpuz0OHJKzX2O1LWTNl"
bucket_name = "infonews"  # 存储空间名称


def img_upload(data):
    """
    文件上传
    :param data: 上传的文件内容
    :return: 生成的文件名
    """
    import qiniu

    q = qiniu.Auth(access_key, secret_key)
    key = None  # 文件名, 如果不设置, 会生成随机文件名
    token = q.upload_token(bucket_name)
    # 上传文件
    ret, info = qiniu.put_data(token, key, data)
    if ret is not None:
        # 返回文件名
        return ret.get("key")  # 获取生成的随机文件名

    else:
        raise BaseException(info)

import random
import re
from datetime import datetime
from info import sr, db
from flask import request, current_app, make_response, jsonify, session

from info.lib.yuntongxun.sms import CCP
from info.models import User
from info.modules.passport import passport_blu
from info.utils.captcha.pic_captcha import captcha
from info.utils.response_code import RET, error_map


# 2使用蓝图注册路由
# 获取图片验证码
@passport_blu.route('/get_img_code')
def get_img_code():
    # 获取参数
    img_code_id = request.args.get('img_code_id')
    # 校验参数
    if not img_code_id:
        return jsonify(errno=RET.PARAMERR, errmsg=error_map[RET.PARAMERR])
    # 生成图片验证码
    img_name, img_text, img_bytes = captcha.generate_captcha()
    # 保存图片key和验证码文本
    try:
        sr.set("img_code_id" + img_code_id, img_text, ex=180)
    except BaseException as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg=error_map[RET.DBERR])
    # 设置自定义响应头
    response = make_response(img_bytes)  # type:Response
    response.content_type = 'image/jpedg'
    # 返回验证码图片
    return response


# 获取短信验证码
@passport_blu.route('/get_sms_code', methods=['POST'])
def get_sms_code():
    # 获取参数
    mobile = request.json.get('mobile')
    img_code = request.json.get('img_code')
    img_code_id = request.json.get('img_code_id')
    # 校验参数
    if not all([mobile, img_code, img_code_id]):
        # 返回自定义错误信息
        return jsonify(errno=RET.PARAMERR, errmsg=error_map[RET.PARAMERR])
    # 校验电话号码是否合法
    if not re.match(r'1[35678]\d{9}$', mobile):
        return jsonify(errno=RET.PARAMERR, errmsg=error_map[RET.PARAMERR])
    # 根据图片key取出验证码文本
    try:
        real_img_code = sr.get('img_code_id' + img_code_id)
    except BaseException as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg=error_map[RET.DBERR])
    # 验证是否过期
    if not real_img_code:
        return jsonify(errno=RET.PARAMERR, errmsg='验证码已过期')
    # 校验图片验证码文本
    if real_img_code != img_code.upper():
        return jsonify(errno=RET.PARAMERR, errmsg='验证码错误')
    # 判断用户是否存在
    try:
        user = User.query.filter_by(mobile=mobile).first()
    except BaseException as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg=error_map[RET.DBERR])
    if user:
        return jsonify(errno=RET.DATAEXIST, errmsg=error_map[RET.DATAEXIST])
    # 生成随机短信验证码
    sms_code = '%04d' % random.randint(0, 9999)
    current_app.logger.info("短信验证码为: %s" % sms_code)
    # # 发送短信
    # response_code = CCP().send_template_sms(mobile, [sms_code, 5], 1)
    # if response_code != 0:
    #     return jsonify(errno=RET.THIRDERR, errmsg=error_map[RET.THIRDERR])
    # 保存短信验证码
    try:
        sr.set('sms_code_id' + mobile, sms_code, ex=60)
    except BaseException as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg=error_map[RET.DBERR])
    # 返回发送结果
    return jsonify(errno=RET.OK, errmsg=error_map[RET.OK])


# 注册
@passport_blu.route('/register', methods=['POST'])
def register():
    # 获取参数
    mobile = request.json.get('mobile')
    password = request.json.get('password')
    sms_code = request.json.get('sms_code')
    # 校验参数
    if not all([mobile, password, sms_code]):
        return jsonify(errno=RET.PARAMERR, errmsg=error_map[RET.PARAMERR])
    # 校验手机号码格式
    if not re.match(r'1[35678]\d{9}$', mobile):
        return jsonify(errno=RET.PARAMERR, errmsg=error_map[RET.PARAMERR])
    # 根据手机号取出短信验证码
    try:
        real_sms_code = sr.get('sms_code_id' + mobile)
    except BaseException as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg=error_map[RET.DBERR])
    # 校验短信验证码
    if not real_sms_code:
        return jsonify(errno=RET.PARAMERR, errmsg='短信验证码已过期')
    if real_sms_code != sms_code:
        return jsonify(errno=RET.PARAMERR, errmsg='验证码错误')
    # 保存数据
    user = User()
    user.mobile = mobile
    user.password = password
    user.nick_name = mobile
    # 记录最后登录时间
    user.last_login = datetime.now()
    try:
        db.session.add(user)
        db.session.commit()
    except BaseException as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR, errmsg=error_map[RET.DBERR])
    # 状态保持(免密码登录)
    session["user_id"] = user.id
    # 返回结果
    return jsonify(errno=RET.OK, errmsg=error_map[RET.OK])


# 登录
@passport_blu.route('/login', methods=['POST'])
def login():
    # 获取参数
    mobile = request.json.get('mobile')
    password = request.json.get('password')
    # 校验参数
    if not all([mobile, password]):
        return jsonify(errno=RET.PARAMERR, errmsg=error_map[RET.PARAMERR])
    # 根据手机号取出用户模型
    try:
        user = User.query.filter_by(mobile=mobile).first()
    except BaseException as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg=error_map[RET.DBERR])
    # 校验用户是否存在
    if not user:
        return jsonify(errno=RET.USERERR, errmsg=error_map[RET.USERERR])
    # 校验密码是否一致
    if not user.check_password(password):
        return jsonify(errno=RET.PARAMERR, errmsg='用户名或密码错误')
    # 记录最后登录时间
    user.last_login = datetime.now()
    # 状态保持
    session['user_id'] = user.id
    # 将结果以json返回
    return jsonify(errno=RET.OK, errmsg=error_map[RET.OK])


# 退出登录
@passport_blu.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('is_admin', None)
    return jsonify(errno=RET.OK, errmsg=error_map[RET.OK])

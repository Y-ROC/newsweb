from info.comments import user_login_data, img_upload
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

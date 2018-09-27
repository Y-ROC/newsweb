from info import sr
from flask import request, abort, current_app, make_response

from info.modules.passport import passport_blu
from info.utils.captcha.pic_captcha import captcha


# 2使用蓝图注册路由
@passport_blu.route('/get_img_code')
def get_img_code():
    # 获取参数
    img_code_id = request.args.get('img_code_id')
    # 校验参数
    if not img_code_id:
        return abort(403)
    # 生成图片验证码
    img_name, img_text, img_bytes = captcha.generate_captcha()
    # 保存图片key和验证码文本
    try:
        sr.set("img_code_id" + img_code_id, img_text, ex=180)
    except BaseException as e:
        current_app.logger.error(e)
        return abort(500)
    # 设置自定义响应头
    response = make_response(img_bytes)  # type:Response
    response.content_type = 'image/jpedg'
    # 返回验证码图片
    return response

# -- coding: utf-8 --

from . import api
from kesheer.utils.captcha.captcha import captcha
from kesheer import redis_store
from kesheer import constants
from flask import current_app, jsonify, make_response
from kesheer.utils.response_code import RET


# GET 127.0.0.1/api/v1.0/image_codes/<image_code_id>
@api.route("/image_codes/<image_code_id>")
def get_image_code(image_code_id):
    """
    获取图片验证码
    : params image_codes_id:  图片验证码编号
    :return: 正常：验证码图片  异常：返回json
    """
    # 业务逻辑处理
    # 生成验证码图片
    # 名字，真实文本，图片数据
    name, text, image_data = captcha.generate_captcha()
    # 将验证码真实值与编号保存到redis中，设置有效期
    # redis:  字符串   列表   哈希  set
    # "key": xxx
    # 使用哈希维护有效期的时候只能整体设置过期时间
    # "image_codes": {"id1"："bac"，"id2"："cdf"，...} 哈希
    # hset("image_codes", "id1", "abc")  # 存
    # hget("image_codes","id1")  # 取

    # SETEX key seconds value
    # 以下两个命令相当于上面一个
    # $redis->SET('key', 'value');
    # $redis->EXPIRE('key','seconds');  # 设置生存时间

    # 单条维护记录，选用字符串类型
    # "image_code_编号1"："真实值文本"
    # "image_code_编号2"："真实值文本"

    # redis_store.set("image_code_%s" % image_code_id, text)
    # redis_store.expire("image_code_%s" % image_code_id, constants.IMAGE_CODE_REDIS_EXPIRE)
    # 将上面两步结合为一步（设置值的同时设置有效期）
    #                                          记录名字                    有效期                记录文本
    try:
        redis_store.setex("image_code_%s" % image_code_id, constants.IMAGE_CODE_REDIS_EXPIRES, text)
    except Exception as e:
        # 记录日志
        current_app.logger.error(e)
        # return jsonify(errno=RET.DBERR, errmsg="save image code id failed")
        return jsonify(errno=RET.DBERR, errmsg="保存图片验证码失败")

    # 返回图片
    resp = make_response(image_data)
    resp.headers["Content-Type"] = "image/jpg"
    return resp





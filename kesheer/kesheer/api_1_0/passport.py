# -- coding: utf-8 --

from . import api
from flask import request, jsonify, current_app, session
from kesheer.utils.response_code import RET
from kesheer import redis_store, db, constants
from kesheer.models import User
from sqlalchemy.exc import IntegrityError
import re


@api.route("/users", methods=["POST"])
def register():
    """注册
       请求参数：手机号、短信验证码、密码、确认密码
       参数格式：json
    """
    # 获取请求的json数据，返回字典
    req_dict = request.get_json()
    mobile = req_dict.get("mobile")
    sms_code = req_dict.get("sms_code")
    password = req_dict.get("password")
    password2 = req_dict.get("password2")

    # 校验参数
    if not all([mobile, sms_code, password, password2]):
        return jsonify(errno=RET.PARAMERR, errmsg="参数不完整")

    # 判断手机号格式
    if not re.match(r"1[34578]\d{9}", mobile):
        # 表示格式不对
        return jsonify(errno=RET.PARAMERR, errmsg="手机号格式错误")

    if password != password2:
        return jsonify(errno=RET.PARAMERR, errmsg="两次密码不一致")

    # 从redis中取出短信验证码
    try:
        real_sms_code = redis_store.get("sms_code_%s" % mobile).decode('utf-8')
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="读取真实验证码异常")

    # 判断短信验证码是否过期
    if real_sms_code is None:
        return jsonify(errno=RET.NODATA, errmsg="短信验证码失效")

    # 删除redis中的短信验证码，防止重复使用校验
    try:
        redis_store.delete("sms_code_%s" % mobile)
    except Exception as e:
        current_app.logger.error(e)

    # 判断用户填写短信验证码的正确性
    if real_sms_code != sms_code:
        return jsonify(errno=RET.DATAERR, errmsg="短信验证错误")

    # 判断用户手机号是否注册过
    """
    由于mobile字段设置唯一索引，所以当用户再次注册时数据库会报错，
    利用保存用户信息到数据库时的报错信息进行异常捕获，来返回错误信息，
    这样减少了一次数据库查询（逻辑优化）
    """
    # try:
    #     user = User.query.filter_by(mobile=mobile).first()
    # except Exception as e:
    #     current_app.logger.error(e)
    #     return jsonify(errno=RET.DBERR, errmsg="数据库异常")
    # else:
    #     if user is not None:
    #         # 手机号已存在
    #         return jsonify(errno=RET.DATAEXIST, errmsg="手机号已存在")

    # 保存用户的注册数据到数据库
    user = User(name=mobile, mobile=mobile)
    user.password = password  # 设置属性
    try:
        db.session.add(user)
        db.session.commit()
        # IntegrityError:数据库重复值异常
    except IntegrityError as e:
        # 数据库操作异常，事务回滚
        db.session.rollback()
        # 表示手机号出现了重复，即手机号已经注册过
        current_app.logger.error(e)
        return jsonify(errno=RET.DATAEXIST, errmsg="手机号已存在")
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(e)
        return jsonify(errno=RET.DATAEXIST, errmsg="查询收据库异常")

    # 保存登录状态到session中
    session["name"] = mobile
    session["mobile"] = mobile
    session["id"] = user.id

    # 返回结果
    return jsonify(errno=RET.OK, errmsg="注册成功")
# -- coding: utf-8 --
from kesheer.utils.image_storage import storage
from flask import g, current_app, request, jsonify, session

from . import api
from kesheer.utils.commons import login_required
from kesheer.utils.response_code import RET
from kesheer.models import User
from kesheer import db, constants


@api.route("/users/avatar", methods=["POST"])
@login_required
def set_user_avatar():
    """
    设置用户头像
    :param 图片（多媒体表单）、用户id（g.user_id）
    :return:
    """
    # 装饰器代码中将user_id保存到g对象中的，视图直接获取
    user_id = g.user_id
    # 获取图片
    image_file = request.files.get("avatar")

    if image_file is None:
        return jsonify(errno=RET.PARAMERR, errmsg="未上传图片")

    image_data = image_file.read()

    # 使用七牛上传图片，返回文件名
    try:
        file_name = storage(image_data)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.THIRDERR, errmsg="上传图片失败")

    # 保存文件名到数据库中
    try:
        User.query.filter_by(id=user_id).update({"avatar_url": file_name})
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="保存图片失败")

    # 保存成功
    avatar_url = constants.QINIU_URL_DOMIN + file_name
    return jsonify(errno=RET.OK, errmsg="保存图片成功", data={"avatar_url": avatar_url})




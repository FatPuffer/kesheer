# -- coding: utf-8 --
from kesheer.utils.image_storage import storage
from flask import g, current_app, request, jsonify, session
import json

from . import api
from kesheer.utils.commons import login_required
from kesheer.utils.response_code import RET
from kesheer.models import Area
from kesheer import db, constants, redis_store


@api.route('/areas')
def get_area_info():
    """获取城区信息"""

    # 尝试从redis中读取数据
    try:
        resp_json = redis_store.get("area_info")
    except Exception as e:
        current_app.logger.error(e)
    else:
        if resp_json is not None:
            # redis有缓存数据
            current_app.logger.info("hit redis area_info")
            return resp_json, 200, {"Content-Type": "aplication/json"}

    # 查询数据库，读取城区信息
    try:
        area_list = Area.query.all()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='数据库异常')

    area_dict_lit = []
    # 将对象转换为字典
    for area in area_list:
        area_dict_lit.append(area.to_dict())

    # 将数据转换为json字符串
    resp_dict = dict(errno=RET.OK, errmsg="OK", data=area_dict_lit)
    resp_json = json.dumps(resp_dict)

    # 将数据保存进redis中
    try:
        redis_store.setex("area_info", constants.AREA_INFO_REDIS_CACHE_EXPIRES, resp_json)
    except Exception as e:
        current_app.logger.error(e)

    return resp_json, 200, {"Content-Type": "aplication/json"}
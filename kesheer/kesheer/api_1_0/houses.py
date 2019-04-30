# -- coding: utf-8 --
from kesheer.utils.image_storage import storage
from flask import g, current_app, request, jsonify, session
import json

from . import api
from kesheer.utils.commons import login_required
from kesheer.utils.response_code import RET
from kesheer.models import Area, House, Facility, HouseImage
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


@api.route("/houses/info", methods=["POST"])
@login_required
def save_house_info():
    """保存房屋基本信息"""
    # 获取数据
    user_id = g.user_id
    house_data = request.get_json()
    title = house_data.get("title")  # 房屋名称
    price = house_data.get("price")  # 房屋价格
    area_id = house_data.get("area_id")  # 房屋所属区域编号
    address = house_data.get("address")  # 房屋地址
    room_count = house_data.get("room_count")  # 房屋总房间数
    acreage = house_data.get("acreage")  # 房屋面积
    unit = house_data.get("unit")  # 房屋布局
    capacity = house_data.get("capacity")  # 房屋容纳人数
    beds = house_data.get("beds")  # 房屋床铺数量
    deposit = house_data.get("deposit")  # 房屋押金
    min_days = house_data.get("min_days")  # 房屋最小入住天数
    max_days = house_data.get("max_days")  # 房屋最大入住天数

    # 参数校验
    if not all([title, price, area_id, address, room_count, acreage, unit, capacity, beds, deposit, min_days, max_days]):
        return jsonify(errno=RET.PARAMERR, errmsg="参数不完整")

    # 判断金额是否正确
    try:
        price = int(float(price)*100)
        deposit = int(float(deposit)*100)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")

    # 判断城区id是否存在
    try:
        area = Area.query.get(area_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="数据库异常")
    if area is None:
        return jsonify(errno=RET.NODATA, errmsg="城区信息有误")

    # 保存房屋信息
    house = House(
        user_id=user_id,
        area_id=area_id,
        title=title,
        price=price,
        address=address,
        room_count=room_count,
        acreage=acreage,
        unit=unit,
        capacity=capacity,
        beds=beds,
        deposit=deposit,
        min_days=min_days,
        max_days=max_days
    )

    # 处理房屋设施信息
    facility_ids = house_data.get("facility")

    # 入果用户勾选了设置信息，再保存数据库
    if facility_ids:
        try:
            facilities = Facility.query.filter(Facility.id.in_(facility_ids)).all()
        except Exception as e:
            current_app.logger.error(e)
            return jsonify(errno=RET.BDERR, errmsg="数据库异常")
        if facilities:
            # 表示有合法的设施数据
            # 保存设施数据
            house.facilities = facilities
    try:
        db.session.add(house)
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=RET.BDERR, errmsg="保存数据失败")

    # 保存数据成功
    return jsonify(errno=RET.OK, errmsg="OK", data={"house_id": house.id})


@api.route("/houses/image", methods=["POST"])
@login_required
def save_house_image():
    """保存房屋的图片
    参数：图片、房屋id
    """
    image_file = request.files.get("house_image")
    house_id = request.form.get("house_id")

    if not all([image_file, house_id]):
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")

    # 判断房子是否存在（house_id的正确性）
    try:
        house = House.query.get("house_id")
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.BDERR, errmsg="数据库异常")

    if house is None:
        return jsonify(errno=RET.NODATA, errmsg="房屋不存在")

    image_data = image_file.read()
    # 保存图片到七牛云中
    try:
        file_name = storage(image_data)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.THIRDERR, errmsg="保存七牛失败")
    # 保存图片信息到数据库
    house_image = HouseImage(house_id=house_id, url=file_name)
    db.session.add(house_image)

    # 处理房屋主图片
    if not house.index_image_url:
        house.index_image_url = file_name
        db.session.add(house)
    try:
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR, errmsg="保存图片数据库异常")

    image_url = constants.QINIU_URL_DOMIN + file_name
    return jsonify(errno=RET.THIRDERR, errmsg="OK", data={"image_url": image_url})
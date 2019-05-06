# -- coding: utf-8 --
from kesheer.utils.image_storage import storage
from flask import g, current_app, request, jsonify, session
import json
from datetime import datetime

from . import api
from kesheer.utils.commons import login_required
from kesheer.utils.response_code import RET
from kesheer.models import Area, House, Facility, HouseImage, Order
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


@api.route("/houses/index", methods=["GET"])
def get_house_index():
    """获取主页幻灯片展示的房屋基本信息"""
    # 从缓存中尝试获取数据
    try:
        ret = redis_store.get("home_page_data")
    except Exception as e:
        current_app.logger.error(e)
        # 初始化ret，也可以将if判断写在else中
        ret = None

    if ret:
        current_app.logger.info("hit house index info redis")
        # 因为redis中保存的是json字符串，所以直接进行字符串拼接返回
        return '{"errno":0, "errmsg":"OK", "data":%s}' % ret, 200, {"Content-Type": "application/json"}
    else:
        try:
            # 查询数据库，返回房屋订单数目最多的5条数据（返回列表）
            houses = House.query.order_by(House.order_count.desc()).limit(constants.HOME_PAGE_MAX_HOUSES)
        except Exception as e:
            current_app.logger.error(e)
            return jsonify(errno=RET.DBERR, errmsg="查询数据失败")

        if not houses:
            return jsonify(errno=RET.NODATA, errmsg="查询无数据")

        houses_list = []
        for house in houses:
            # 如果房屋未设置主图片，则跳过
            if not house.index_image_url:
                continue
            houses_list.append(house.to_basic_dict())

        # 将数据转换为json，并保存到redis缓存
        json_houses = json.dumps(houses_list)  # "[{},{},{}]"
        try:
            redis_store.setex("home_page_data", constants.HOME_PAGE_DATA_REDIS_EXPIRES, json_houses)
        except Exception as e:
            current_app.logger.error(e)

        return '{"errno":0, "errmsg":"OK", "data":%s}' % json_houses, 200, {"Content-Type": "application/json"}


@api.route("/houses/<int:house_id>", methods=["GET"])
def get_house_detail(house_id):
    """获取房屋详情"""
    # 前端在房屋详情页面展示时，如果浏览页面的用户不是该房屋的房东，则展示预定按钮，否则不展示，
    # 所以需要后端返回登录用户的user_id
    # 尝试获取用户登录的信息，若登录，则返回给前端登录用户的user_id，否则返回user_id=-1
    user_id = session.get("user_id", "-1")

    # 校验参数
    if not house_id:
        return jsonify(errno=RET.PARAMERR, errmsg="参数确缺失")

    # 先从redis缓存中获取信息
    try:
        ret = redis_store.get("house_info_%s" % house_id)
    except Exception as e:
        current_app.logger.error(e)
        ret = None
    if ret:
        current_app.logger.info("hit house info redis")
        return '{"errno":"0", "errmsg":"OK", "data":{"user_id":%s, "house":%s}}' % (user_id, ret), \
               200, {"Content-Type": "application/json"}

    # 查询数据库
    try:
        house = House.query.get(house_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="查询数据失败")

    if not house:
        return jsonify(errno=RET.NODATA, errmsg="房屋不存在")

    # 将房屋对象数据转换为字典
    try:
        house_data = house.to_full_dict()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DATAERR, errmsg="数据出错")

    # 存入到redis中
    json_house = json.dumps(house_data)
    try:
        redis_store.setex("house_info_%s" % house_id, constants.HOUSE_DETAIL_REDIS_EXPIRE_SECOND, json_house)
    except Exception as e:
        current_app.logger.error(e)

    resp = '{"errno":"0", "errmsg":"OK", "data":{"user_id":%s, "house":%s}}' % (user_id, json_house), \
           200, {"Content-Type": "application/json"}
    return resp


# GET /api/v1.0/houses?sd=2019-05-05&ed=2019-05-sa06&id=2&sk=new&p=1
@api.route("/houses")
def get_houxe_list():
    """
    获取房屋的列表信息（搜索页面）
    起始日期\房屋id\排序规则\页码
    :return:
    """
    start_date = request.args.get('sd')
    end_date = request.args.get('ed')
    area_id = request.args.get('id')
    # 如果用户未选择排序，我们默认使用最新上线排序
    sort_key = request.args.get('sk', 'new')
    page = request.args.get('p')

    # 处理时间
    try:
        if start_date:
            """
            datetime.strftime():将时间类型转换为字符串
            datetime.strptime():将字符串转换为时间类型
            """
            start_date = datetime.strptime(start_date, "%Y-%m-%d")

        if end_date:
            end_date = datetime.strptime(end_date, "%Y-%m-%d")

        if start_date and end_date:
            assert start_date <= end_date
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.PARAMERR, errmsg="日期参数错误")

    # 判断区域id
    if area_id:
        try:
            area = Area.query.get(area_id)
        except Exception as e:
            current_app.logger.error(e)
            return jsonify(errno=RET.PARAMERR, errmsg="区域参数错误")

    # 处理页数
    try:
        page = int(page)
    except Exception as e:
        current_app.logger.error(e)
        page = 1

    # 过滤条件参数容器
    filter_params = []

    # 填充过滤参数
    # 时间条件
    conflict_orders = None

    try:
        if start_date and end_date:
            # 指定起始时间查询冲突的订单
            conflict_orders = Order.query.filter(Order.begin_date <= end_date, Order.end_date >= start_date).all()

        elif start_date:
            # 指定开始时间查询冲突的订单
            conflict_orders = Order.query.filter(Order.end_date >= start_date).all()

        elif end_date:
            # 指定结束时间查询冲突的订单
            conflict_orders = Order.query.filter(Order.begin_date <= end_date).all()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='数据库异常')

    if conflict_orders:
        # 从订单表中获取冲突房屋的id
        conflict_house_ids = [order.house_id for order in conflict_orders]

        # 如果没有冲突的房屋id,向查询参数中添加条件
        if conflict_house_ids:
            filter_params.append(House.id.notin_(conflict_house_ids))

    # 区域条件
    if area_id:
        # [<sqlalchemy.sql.elements.BinaryExpression object at 0x7fd30379bfd0>]
        # House.area_id.__eq__(1)
        # == : __eq__
        # dir(House.area_id) : 在ipython下执行，可以查看所有可以使用的方法
        filter_params.append(House.area_id == area_id)

    # 查询数据库
    # 补充排序条件
    if sort_key == 'booking':
        house_query = House.query.filter(*filter_params).order_by(House.order_count.desc())
    elif sort_key == 'price-inc':
        house_query = House.query.filter(*filter_params).order_by(House.price.asc())
    elif sort_key == 'price-des':
        house_query = House.query.filter(*filter_params).order_by(House.price.desc())
    else:  # 最新上线
        house_query = House.query.filter(*filter_params).order_by(House.create_time.desc())

    # 处理分页
    #                                当前页数                   每页数据量                       自动的错误输出
    try:
        page_obj = house_query.paginate(page=page, per_page=constants.HOUSE_LIST_PAGE_CAPACITY, error_out=False)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='数据库异常')

    # 获取页面数据
    house_list = page_obj.items
    houses = []
    for house in house_list:
        houses.append(house.to_basic_dict())

    # 获取总页数
    total_page = page_obj.pages

    return jsonify(errno=RET.OK, errmsg='OK', data={'total_page': total_page, 'houses': houses, 'current_page': page})









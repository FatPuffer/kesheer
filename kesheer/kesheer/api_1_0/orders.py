# coding:utf-8

import datetime
from flask import request, g, jsonify, current_app

from kesheer import db, redis_store
from kesheer.utils.commons import login_required
from kesheer.utils.response_code import RET
from kesheer.models import House, Order
from . import api


@api.route("/orders", methods=["GET", "POST"])
@login_required
def save_order():
    """保存订单"""
    user_id = g.user_id
    # 获取参数
    order_data = request.get_json()
    if not order_data:
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")

    house_id = order_data.get("house_id")  # 预定房屋的编号
    start_date_str = order_data.get("start_date")  # 预定房屋的开始时间
    end_date_str = order_data.get("end_date")  # 预定房屋的结束时间

    # 参数校验
    if not all([house_id, start_date_str, end_date_str]):
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")

    # 日期格式检查
    try:
        # 将请求的时间字符串转换为datetime类型
        start_date = datetime.datetime.strptime(start_date_str, "%Y-%m-%d")
        end_date = datetime.datetime.strptime(end_date_str, "%Y-%m-%d")
        assert start_date <= end_date
        # 计算预定天数
        # .days:获取天数
        # .years:获取年数
        days = (end_date - start_date).days + 1
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.PARAMERR, errmsg="日期格式错误")

    # 查询房屋是否存在
    try:
        house = House.query.get(house_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="获取房屋信息失败")
    if not house:
        return jsonify(errno=RET.NODATA, errmsg="房屋不存在")

    # 预定房屋是否是房东自己的
    if user_id == house.user_id:
        return jsonify(errno=RET.ROLEERR, errmsg="不能预定自己的房屋")

    # 确保用户预定的时间内，房屋没有被别人下单
    try:
        # 查询时间冲突的订单数
        count = Order.query.filter(Order.house_id == house_id, Order.begin_date <= end_date,
                                   Order.end_date >= start_date).count()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="检查出错，请稍后重试")
    if count > 0:
        return jsonify(errno=RET.DATAERR, errmsg="房屋已被预定")

    # 订单总金额
    amount = days * house.price

    # 保存订单数据
    order = Order(
        house_id=house_id,
        user_id=user_id,
        begin_date=start_date,
        end_date=end_date,
        days=days,
        house_price=house.price,
        amount=amount
    )

    try:
        db.session.add(order)
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR, errmsg="保存订单失败")
    return jsonify(errno=RET.OK, errmsg="OK", data={"order_id": order.id})


# /api/v1.0/user/orders?role=custom
#                       role=landlord
@api.route("/user/orders", methods=["GET"])
@login_required
def get_user_orders():
    """查询用户订单信息"""
    user_id = g.user_id

    # 用户的身份信息，用户想要查询作为房客预定别人房子的订单，还是想要作为房东查询别人预定自己房子的订单
    role = request.args.get("role", "")
    # 查询订单数据
    try:
        if "landlord" == role:
            # 以房东的身份查询订单
            # 先查询属于自己的房子有哪些
            houses = House.query.filter(House.user_id == user_id).all()
            houses_ids = [house.id for house in houses]
            # 再查询预定了自己房子的订单
            orders = Order.query.filter(Order.house_id.in_(houses_ids)).order_by(Order.create_time.desc())
        else:
            # 以房客的身份查询订单，查询自己预定的订单
            orders = Order.query.filter(Order.user_id == user_id).order_by(Order.create_time.desc())
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="查询订单信息失败")

    # 将订单对象转换为字典数据
    order_dict_list = []
    if orders:
        for order in orders:
            order_dict_list.append(order.to_dict())

    return jsonify(errno=RET.OK, errmsg="OK", data={"orders": order_dict_list})


@api.route("/orders/<int:order_id>/status", methods=["PUT"])
@login_required
def accept_reject_order(order_id):
    """接单、拒单"""
    user_id = g.user_id

    # 获取参数
    req_data = request.get_json()
    if not req_data:
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")

    # action参数表明客户请求的是接单还是拒单行为
    action = req_data.get("action")
    if action not in ("accept", "reject"):
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")

    try:
        # 根据订单号查询订单，并且要求订单处于等待接单状态
        order = Order.query.filter(Order.id == order_id, Order.status == "WAIT_ACCEPT").first()
        # 获取订单里的房屋对象
        house = order.house
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.PARAMERR, errmsg="无法获取订单数据")

    # 确保房东只能修改属于自己的房子的订单
    # 判断订单房屋的user_id是不是用户id
    if not order or house.user_id != user_id:
        return jsonify(errno=RET.REQERR, errmsg="操作无效")

    if action == "accept":
        # 接单，将订单状态设置为等待评论
        order.status = "WAIT_PAYMENT"
    elif action == "reject":
        # 拒单，要求用户传递拒单原因
        reason = req_data.get("reason")
        if not reason:
            return jsonify(errno=RET.PARAMERR, errmsg="参数错误")
        order.status = "REJECTED"
        order.comment = reason
    try:
        db.session.add(order)
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR, errmsg="操作失败")

    return jsonify(errno=RET.OK, errmsg="OK")


@api.route("/orders/<int:order_id>/comment", methods=["PUT"])
@login_required
def save_order_comment(order_id):
    """订单评论"""
    user_id = g.user_id
    # 获取参数
    req_data = request.get_json()
    comment = req_data.get("comment")
    print 111111111111111111
    print comment
    # 检查参数
    if not comment:
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")

    try:
        # 需要确保只能评论自己下的订单，而且订单处于待评价状态才可以
        order = Order.query.filter(Order.id == order_id, Order.user_id == user_id,
                                   Order.status == "WAIT_COMMENT").first()
        house = order.house
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="无法获取订单数据")

    if not order:
        return jsonify(errno=RET.REQERR, errmsg="操作无效")

    try:
        # 将订单状态设置为已完成
        order.status = "COMPLETE"
        # 保存订单的评论信息
        order.comment = comment
        # 将房屋的完成订单数增加1
        house.order_count += 1
        db.session.add(order)
        db.session.add(house)
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR, errmsg="操作无效")

    # 因为房屋详情中由订单的评论信息，为了让最新的评价信息展示在房屋详情中，所以删除redis中关于本订单房屋的详情信息缓存数据
    try:
        redis_store.delete("house_info_%s" % order.house_id)
    except Exception as e:
        current_app.logget.error(e)

    return jsonify(errno=RET.OK, errmsg="OK")

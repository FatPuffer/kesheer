# -- coding: utf-8 --

from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from . import db
from kesheer import constants


class BaseModel(object):
    """模型基类，为每个模型补充创建时间与更新时间"""

    create_time = db.Column(db.DateTime, default=datetime.now())  # 记录的创建时间
    update_time = db.Column(db.DateTime, default=datetime.now(), onupdate=datetime.now())  # 记录的更新时间


class User(BaseModel, db.Model):
    """用户"""

    __tablename__ = "ks_user_profile"

    id = db.Column(db.Integer, primary_key=True)  # 用户编号
    name = db.Column(db.String(32), unique=True, nullable=False)  # 用户昵称
    password_hash = db.Column(db.String(128), nullable=False)  # 用户密码
    mobile = db.Column(db.String(11), unique=True, nullable=False)  # 用户手机
    real_name = db.Column(db.String(32))  # 真实姓名
    id_card = db.Column(db.String(20))  # 用户身份证号
    avatar_url = db.Column(db.String(128))  # 用户头像路径
    houses = db.relationship("House", backref="user")  # 用户发布的房源信息
    orders = db.relationship("Order", backref="user")  # 用户订单信息

    # 加上property装饰器后，会把函数变为属性，属性名即为函数名
    @property
    def password(self):
        """读取属性的函数行为"""
        # print(user.password)  #读取属性时被调用
        # 函数的返回值作为属性值返回
        # return "xxxx"
        raise ArithmeticError("这个属性只能设置，不能被读取")

    # 使用这个装饰器，对应设置属性操作
    @password.setter
    def password(self, value):
        """
        设置属性 user.password = "xxxxx"
        :param value: 设置属性时的数据 value就是"xxxxx",原始的明文密码
        :return:
        """
        self.password_hash = generate_password_hash(value)

    def check_password(self, passwd):
        """
        检验密码的正确性
        :param passwd: 用户登录时填写的原始密码
        :return: 如果正确，返回True，否则返回False
        """
        return check_password_hash(self.password_hash, passwd)

    def to_dict(self):
        """将对象转换为字典数据"""
        user_dict = {
            "user_id": self.id,
            "name": self.name,
            "mobile": self.mobile,
            "avatar": constants.QINIU_URL_DOMIN + self.avatar_url if self.avatar_url else "",
            "create_time": self.create_time.strftime("%Y-%m-%d %H:%M:%S")
        }
        return user_dict

    def auth_to_dict(self):
        auth_dict = {
            "user_id": self.id,
            "real_name": self.real_name,
            "id_card": self.id_card
        }
        return auth_dict


class Area(BaseModel, db.Model):
    """城区"""

    __tablename__ = "ks_area_info"

    id = db.Column(db.Integer, primary_key=True)  # 区域编号
    name = db.Column(db.String(32), nullable=False)  # 区域名字
    houses = db.relationship("House", backref="area")  # 区域的房屋

    def to_dict(self):
        """将对象转换为字典"""
        d = {
            "aid": self.id,
            "aname": self.name
        }
        return d


# 房屋设施表，建立房屋与设施的多对多关系
house_facility = db.Table(
    "ks_house_facility",
    db.Column("house_id", db.Integer, db.ForeignKey("ks_house_info.id"), primary_key=True),  # 房屋编号
    db.Column("facility_id", db.Integer, db.ForeignKey("ks_facility_info.id"), primary_key=True),  # 设施编号
)


class House(BaseModel,db.Model):
    """房屋信息"""

    __tablename__ = "ks_house_info"

    id = db.Column(db.Integer, primary_key=True)  # 房屋编号
    user_id = db.Column(db.Integer, db.ForeignKey("ks_user_profile.id"), nullable=False)  # 房主的用户编号
    area_id = db.Column(db.Integer, db.ForeignKey("ks_area_info.id"), nullable=False)  # 所属区域编号
    title = db.Column(db.String(64), nullable=False)  # 标题
    price = db.Column(db.Integer, default=0)  # 单价，单位元
    address = db.Column(db.String(512), default="")  # 地址
    room_count = db.Column(db.Integer, default=1)  # 房间数量
    acreage = db.Column(db.Integer, default=0)  # 房屋面积
    unit = db.Column(db.String(32), default="")  # 房屋单元，如：几室几厅
    capacity = db.Column(db.Integer, default=1)  # 房屋容纳人数
    beds = db.Column(db.String(64), default="")  # 房屋床铺数量
    deposit = db.Column(db.Integer, default=0)  # 房屋押金
    min_days = db.Column(db.Integer, default=1)  # 最小入住天数
    max_days = db.Column(db.Integer, default=0)  # 最多入住天数，0表示不限制
    order_count = db.Column(db.Integer, default=0)  # 该房屋完成预定的订单数
    index_image_url = db.Column(db.String(256), default="")  # 房屋主图片路径
    # 外键关联Facility（设施表），查询时通过house_facility（第三张表）
    facilities = db.relationship("Facility", secondary=house_facility)  # 房屋的设施
    images = db.relationship("HouseImage")  # 房屋的图片
    orders = db.relationship("Order", backref="house")  # 房屋订单

    def to_basic_dict(self):
        """将基本信息转换为字典数据"""
        house_dict = {
            "house_id": self.id,
            "title": self.title,
            "price": self.price,
            "area_name": self.area.name,
            "img_url": constants.QINIU_URL_DOMIN + self.index_image_url if self.user.avatar_url else "",
            "room_count": self.room_count,
            "order_count": self.order_count,
            "address": self.address,
            "user_avatar": constants.QINIU_URL_DOMIN + self.user.avatar_url if self.user.avatar_url else "",
            "ctime": self.create_time.strftime("%Y-%m-%d")
        }
        return house_dict

    def to_full_dict(self):
        """将详细信息转换为字典数据"""
        house_dict = {
            "hid": self.id,
            "user_id": self.user_id,
            "user_name": self.user.name,
            "user_avatar": constants.QINIU_URL_DOMIN + self.user.avatar_url if self.user.avatar_url else "",
            "title": self.title,
            "price": self.price,
            "address": self.address,
            "room_count": self.room_count,
            "acreage": self.acreage,
            "unit": self.unit,
            "capacity": self.capacity,
            "beds": self.beds,
            "deposit": self.deposit,
            "max_days": self.max_days,
            "min_days": self.min_days,
        }

        # 房屋图片
        img_urls = []
        for image in self.images:
            img_urls.append(constants.QINIU_URL_DOMIN + image.url)
        house_dict["img_urls"] = img_urls

        # 房屋设施
        facilities = []
        for facility in self.facilities:
            facilities.append(facility.id)
        house_dict["facilities"] = facilities

        comments = []
        orders = Order.query.filter(Order.house_id == self.id, Order.status == "COMPLETE", Order.comment != None)\
            .order_by(Order.update_time.desc()).limit(constants.HOUSE_DETAIL_COMMENT_DISPLAY_COUNTS)
        for order in orders:
            comment = {
                "comment": order.comment,  # 评论内容
                "user_name": order.user.name if order.user.name != order.user.mobile else "匿名用户",  # 评论用户
                "ctime": order.update_time.strftime("%Y-%m-%d %H:%M:%S")  # 评论时间
            }
            comments.append(comment)
        house_dict["comments"] = comments
        return house_dict


class Facility(BaseModel,db.Model):
    """设施信息"""

    __tablename__ = "ks_facility_info"

    id = db.Column(db.Integer, primary_key=True)  # 设施编号
    name = db.Column(db.String(32), nullable=False)  # 设施名称


class HouseImage(BaseModel, db.Model):
    """房屋图片"""

    __tablename__ = "ks_house_image"

    id = db.Column(db.Integer, primary_key=True)  # 图片编号
    house_id = db.Column(db.Integer, db.ForeignKey("ks_house_info.id"), nullable=False)  # 房屋编号
    url = db.Column(db.String(32), nullable=False)  # 图片路径


class Order(BaseModel, db.Model):
    """订单"""

    __tablename__ = "ks_order_info"

    id = db.Column(db.Integer, primary_key=True)  # 订单编号
    user_id = db.Column(db.Integer, db.ForeignKey("ks_user_profile.id"), nullable=False)  # 下单用户编号
    house_id = db.Column(db.Integer, db.ForeignKey("ks_house_info.id"), nullable=False)  # 下单房间编号
    begin_date = db.Column(db.DateTime, nullable=False)  # 预定起始时间
    end_date = db.Column(db.DateTime, nullable=False)  # 预定结束时间
    days = db.Column(db.Integer, nullable=False)  # 预定的总天数
    house_price = db.Column(db.Integer, nullable=False)  # 预定时的房屋单价
    amount = db.Column(db.Integer, nullable=False)  # 订单总金额
    status = db.Column(
        db.Enum(
            "WAIT_ACCEPT",  # 待接单
            "WAIT_PAYMENT",  # 代付款
            "PAID",  # 已支付
            "WAIT_COMMENT",  # 待评价
            "COMPLETE",  # 已完成
            "CANCELED",  # 已取消
            "REJECTED",  # 已拒单
        ),
        default="WAIT_ACCEPT", index=True)
    comment = db.Column(db.Text)  # 订单的评论信息或者拒单原因
    trade_no = db.Column(db.String(80))  # 交易流水号

    def to_dict(self):
        """将订单信息转换为字典数据"""
        order_dict = {
            "order_id": self.id,
            "title": self.house.title,
            "img_url": constants.QINIU_URL_DOMAIN + self.house.index_image_url if self.house.index_image_url else "",
            "start_date": self.begin_date.strftime("%Y-%m-%d"),
            "end_date": self.end_date.strftime("%Y-%m-%d"),
            "ctime": self.create_time.strftime("%Y-%m-%d %H:%M:%S"),
            "days": self.days,
            "amount": self.amount,
            "status": self.status,
            "comment": self.comment if self.comment else ""
        }
        return order_dict

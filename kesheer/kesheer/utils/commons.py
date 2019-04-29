# -- coding: utf-8 --

from flask import session, jsonify, g
from werkzeug.routing import BaseConverter
import functools

from kesheer.utils.response_code import RET


# 定义正则转换器
class ReConverter(BaseConverter):
    """"""
    def __init__(self, url_map, regex):
        # 调用父类初始化方法
        super(ReConverter, self).__init__(url_map)
        # 保存正则表达式
        self.regex = regex


# 定义验证登陆状态的装饰器
def login_required(view_func):

    @functools.wraps(view_func)
    def wrapper(*args, **kwargs):
        # 判断用户登陆状态
        user_id = session.get("user_id")
        print("用户id", user_id)
        # 如果用户是登陆的，直接执行试图函数
        if user_id is not None:
            # 全局g对象，用来传递参数
            g.user_id = user_id
            return view_func(*args, **kwargs)
        else:
            # 如果未登录，返回未登陆信息（如果是前后端不分离，直接跳转登陆页面）
            return jsonify(errno=RET.SESSIONERR, errmsg="用户未登陆")
    return wrapper


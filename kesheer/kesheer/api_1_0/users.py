# -- coding: utf-8 --
from flask import current_app

from kesheer import db, models
from . import api


@api.route('/index')
def index():
    # 调试模式下，我们设置的日志级别不会生效
    current_app.logger.error("error info")
    current_app.logger.warn("warn info")
    current_app.logger.info("info info")
    current_app.logger.debug("debug info")
    return "index page"

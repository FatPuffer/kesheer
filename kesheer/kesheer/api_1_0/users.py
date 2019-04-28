from flask import current_app

from kesheer import db
from . import api


@api.route('/index')
def index():
    current_app.logger.error("error info")
    current_app.logger.warn("warn info")
    current_app.logger.info("info info")
    current_app.logger.debug("debug info")
    return "index page"

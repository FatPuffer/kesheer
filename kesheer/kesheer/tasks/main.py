# -- coding: utf-8 --

from celery import Celery
from kesheer.tasks import config

# 定义celery对象
celery_app = Celery("home")

# 引入配置信息
celery_app.config_from_object(config)

# 自动搜寻异步任务
celery_app.autodiscover_tasks(["kesheer.tasks.sms"])


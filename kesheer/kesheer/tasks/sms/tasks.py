# -- coding: utf-8 --

from kesheer.tasks.main import celery_app
from kesheer.libs.yuntongxun.sms import CCP


@celery_app.task
def send_sms(to, datas, temp_id):
    """发送短信的异步任务"""
    ccp = CCP()
    ccp.send_template_sms(to, datas, temp_id)


# 启动命令： 首先切换到项目启动目录
# celery -A kesheer.tasks.main worker -l info

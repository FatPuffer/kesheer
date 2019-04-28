# -- coding: utf-8 --

from kesheer import create_app, db
from flask_script import Manager  # 数据库脚本管理对象
from flask_migrate import Migrate, MigrateCommand  # 数据库迁移解析对象和执行对象

# 创建flask的应用对象
app = create_app("develope")

# 创建flask脚本管理工具
manager = Manager(app)

# 创建数据库迁移工具对象
Migrate(app, db)

# 向manager对象中添加数据库操作命令
manager.add_command("db", MigrateCommand)

if __name__ == "__main__":
    manager.run()

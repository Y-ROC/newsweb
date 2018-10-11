import datetime
import random

from flask import current_app
from flask_script import Manager
from flask_migrate import MigrateCommand
from info import create_app

app = create_app('dev')
# 创建管理器
mgr = Manager(app)
# 添加迁移命令
mgr.add_command('mc', MigrateCommand)


# 生成管理员命令,先封装成函数.再将函数包装成命令
@mgr.option("-u", dest="username")
@mgr.option("-p", dest="password")
def create_superuser(username, password):
    if not all([username, password]):
        print('参数不足')
        return
    from info.models import User
    from info import db
    user = User()
    user.mobile = username
    user.password = password
    user.nick_name = username
    user.is_admin = True
    # 添加到数据库
    try:
        db.session.add(user)
        db.session.commit()
    except BaseException as e:
        current_app.logger.error(e)
        db.session.rollback()
        print('数据库操作错误')
    print("管理员创建成功")


def add_test_users():
    from info import db
    from info.models import User
    users = []
    now = datetime.datetime.now()
    for num in range(0, 10000):
        try:
            user = User()
            user.nick_name = "%011d" % num
            user.mobile = "%011d" % num
            user.password_hash = "pbkdf2:sha256:50000$SgZPAbEj$a253b9220b7a916e03bf27119d401c48ff4a1c81d7e00644e0aaf6f3a8c55829"
            user.create_time = now - datetime.timedelta(seconds=random.randint(0, 2678400))
            users.append(user)
            print(user.mobile)
        except Exception as e:
            print(e)
    db.session.add_all(users)
    db.session.commit()
    print('OK')

if __name__ == '__main__':
    mgr.run()
    # add_test_users()

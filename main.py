from flask_script import Manager
from flask_migrate import MigrateCommand
from info import create_app

app = create_app('dev')
# 创建管理器
mgr = Manager(app)
# 添加迁移命令
mgr.add_command('mc', MigrateCommand)

if __name__ == '__main__':
    mgr.run()

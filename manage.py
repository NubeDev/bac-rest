from flask_migrate import MigrateCommand, Migrate
from flask_script import Manager

from src import db, AppSetting, GunicornFlaskApplication

setting = AppSetting().reload(AppSetting.default_setting_file)
app = GunicornFlaskApplication(setting, {}).load()

migrate = Migrate(app, db, compare_type=True, render_as_batch=True)

manager = Manager(app)
manager.add_command('db', MigrateCommand)

if __name__ == '__main__':
    manager.run()

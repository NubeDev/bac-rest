from flask_migrate import MigrateCommand, Migrate
from flask_script import Manager

from src import app, db

migrate = Migrate(app, db)

manager = Manager(app)
manager.add_command('db', MigrateCommand)

if __name__ == '__main__':
    manager.run()

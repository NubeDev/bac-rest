### Commands

1. Initializes migration support for the application (only for the first time):
   > python manage.py db init

2. Create migration script of schema change (The generated script should to be reviewed and edited as not all types of 
   changes can be detected automatically. [For more details](https://alembic.sqlalchemy.org/en/latest/autogenerate.html#what-does-autogenerate-detect-and-what-does-it-not-detect)):
   > python manage.py db migrate

3. Apply the migration to the DB:
   > python manage.py db upgrade
   
3. Revert the migration to the DB:
   > python manage.py db downgrade

4. Migration command-line help:
   > python manage.py db --help


#### [For more details](https://flask-migrate.readthedocs.io/en/latest/)

from sqlalchemy import inspect

from src import db


class SettingBaseModel(db.Model):
    __abstract__ = True

    created_on = db.Column(db.DateTime, server_default=db.func.now())
    updated_on = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now())

    @classmethod
    def find_all(cls):
        return cls.query.all()

    @classmethod
    def find_one(cls):
        return cls.query.first()

    def save_to_db(self):
        db.session.add(self)
        db.session.commit()

    def delete_from_db(self):
        db.session.delete(self)
        db.session.commit()

    # Issue #85 filter_by(...).update(...) is not working in inheritance
    def update(self, **kwargs):
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        changed: bool = self.inspect_changes()
        db.session.commit()
        return changed

    def inspect_changes(self) -> bool:
        for attr in inspect(self).attrs:
            if attr.history.has_changes():
                return True
        return False

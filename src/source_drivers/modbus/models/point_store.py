from src import db


class ModbusPointStoreModel(db.Model):
    __tablename__ = 'mod_points_store'
    # id = db.Column(db.Integer(), primary_key=True, nullable=False, autoincrement=True)
    point_uuid = db.Column(db.String, db.ForeignKey('mod_points.uuid'), primary_key=True, nullable=False)
    value = db.Column(db.Float(), nullable=False)
    value_array = db.Column(db.String())
    fault = db.Column(db.Boolean(), default=False, nullable=False)
    fault_message = db.Column(db.String())
    ts = db.Column(db.DateTime, server_default=db.func.now())

    def __repr__(self):
        return f"ModbusPointStore({self.point_uuid})"

    @classmethod
    def find_last_valid_row(cls, point_uuid):
        return cls.query.filter_by(point_uuid=point_uuid, fault=False).order_by(cls.ts.desc()).first()

    def save_to_db(self):
        db.session.add(self)
        db.session.commit()

    def delete_from_db(self):
        db.session.delete(self)
        db.session.commit()

    def update_to_db_cov_only(self):
        if self.value is None:
            return
        db.session.query(ModbusPointStoreModel).filter(ModbusPointStoreModel.point_uuid == self.point_uuid and
                                                       (ModbusPointStoreModel.value != self.value or
                                                        ModbusPointStoreModel.fault == True)) \
            .update({
                ModbusPointStoreModel.value: self.value,
                ModbusPointStoreModel.value_array: self.value_array,
                ModbusPointStoreModel.fault: False,
                ModbusPointStoreModel.fault_message: None,
            })

    def update_with_fault(self):
        db.session.query(ModbusPointStoreModel).filter(ModbusPointStoreModel.point_uuid == self.point_uuid and
                                                       (ModbusPointStoreModel.fault == False or
                                                        ModbusPointStoreModel.fault_message != self.fault_message)) \
            .update({
                ModbusPointStoreModel.fault: self.fault,
                ModbusPointStoreModel.fault_message: self.fault_message,
            })
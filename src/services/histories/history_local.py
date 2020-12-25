from datetime import datetime

from src import db
from src.event_dispatcher import EventDispatcher
from src.interfaces.point import HistoryType
from src.models.device.model_device import DeviceModel
from src.models.network.model_network import NetworkModel
from src.models.point.model_point import PointModel
from src.models.point.model_point_store import PointStoreModel
from src.models.point.model_point_store_history import PointStoreHistoryModel
from src.services.event_service_base import EventServiceBase, EventType
from src.utils import Singleton

SERVICE_NAME_HISTORIES_LOCAL = 'histories_local'


class HistoryLocal(EventServiceBase, metaclass=Singleton):
    """
    A simple history saving protocol for those points which has `history_type=INTERVAL`
    """
    SYNC_PERIOD = 5
    service_name = SERVICE_NAME_HISTORIES_LOCAL
    threaded = True

    binding = None

    def __init__(self):
        super().__init__()
        self.supported_events[EventType.INTERNAL_SERVICE_TIMEOUT] = True
        EventDispatcher().add_service(self)

    def sync_interval(self):
        while True:
            self._set_internal_service_timeout(self.SYNC_PERIOD)
            event = self._event_queue.get()
            if event.event_type is not EventType.INTERNAL_SERVICE_TIMEOUT:
                raise Exception('History Local: invalid event received somehow... should be impossible')
            results = self.__get_all_enabled_interval_points()
            for point, point_store in results:
                latest_point_store_history = PointStoreHistoryModel.get_latest(point.uuid)
                self.__sync_on_interval(point, point_store, latest_point_store_history)

            db.session.commit()

    def __get_all_enabled_interval_points(self):
        return db.session.query(PointModel, PointStoreModel).select_from(PointModel) \
            .filter_by(history_enable=True, history_type=HistoryType.INTERVAL) \
            .join(DeviceModel).filter_by(history_enable=True) \
            .join(NetworkModel).filter_by(history_enable=True) \
            .join(PointStoreModel) \
            .all()

    def __sync_on_interval(self, point: PointModel, point_store: PointStoreModel,
                           latest_point_store_history: PointStoreHistoryModel):
        if not latest_point_store_history:
            # minutes is placing such a way if 15, then it will store values on 0, 15, 30, 45
            minute = int(datetime.utcnow().minute / point.history_interval) * point.history_interval
            point_store.ts = point_store.ts.replace(minute=minute, second=0, microsecond=0)
            point.create_history(point_store)
        elif (datetime.utcnow() - latest_point_store_history.ts).total_seconds() >= point.history_interval * 60:
            point_store.ts = datetime.utcnow().replace(second=0, microsecond=0)
            point.create_history(point_store)

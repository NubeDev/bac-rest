from __future__ import annotations
from src.services.event_service_base import EventServiceBase, EventTypes, Event


class EventDispatcher:

    _instance = None

    def __init__(self):
        if EventDispatcher._instance:
            raise Exception("EventDispatcher class is a singleton class!")
        else:
            EventDispatcher._instance = self
        self.services = []
        self.source_drivers = []

    @classmethod
    def get_instance(cls) -> EventDispatcher:
        if not cls._instance:
            cls()
        return cls._instance

    @classmethod
    def add_service(cls, service: EventServiceBase):
        if isinstance(service, EventServiceBase):
            cls.get_instance().services.append(service)
        else:
            raise Exception('Invalid service type added', service)

    @classmethod
    def add_source_driver(cls, new_driver: EventServiceBase):
        if not isinstance(new_driver, EventServiceBase):
            raise Exception('Invalid driver type added', new_driver)
        else:
            for driver in cls.get_instance().source_drivers:
                if driver.service_name == new_driver.service_name:
                    raise Exception('driver already registered:', new_driver.service_name)
            cls.get_instance().source_drivers.append(new_driver)

    @classmethod
    def dispatch_from_service(cls, origin_service: EventServiceBase, event: Event, source_driver_name: str = None):
        if source_driver_name:
            print('Event dispatcher searching for driver', source_driver_name)
            for driver in cls.get_instance().source_drivers:
                if driver.service_name == source_driver_name:
                    print('Event dispatcher found source driver')
                    driver.add_event(event)
                    break
        for service in cls.get_instance().services:
            if service is not origin_service:
                service.add_event(event)

    @classmethod
    def dispatch_from_source(cls, origin_source_driver: EventServiceBase, event: Event):
        for service in cls.get_instance().services:
            service.add_event(event)
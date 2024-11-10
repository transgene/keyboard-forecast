import datastore


class Location:
    def __init__(self, location_dict: dict):
        self.__location = location_dict

    @property
    def country(self) -> str:
        return self.__location["country"]

    @property
    def city(self) -> str:
        return self.__location["city"]

    @property
    def lat(self) -> float:
        return self.__location["lat"]

    @property
    def lng(self) -> float:
        return self.__location["lng"]

    def __str__(self):
        return f"{self.city}, {self.country} ({self.lat}, {self.lng})"


def get():
    return Location(datastore.get_location())

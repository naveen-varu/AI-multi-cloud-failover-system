from abc import ABC, abstractmethod


class ICloudProvider(ABC):

    @abstractmethod
    def get_health(self, node):
        pass

    @abstractmethod
    def start_node(self, node):
        pass

    @abstractmethod
    def stop_node(self, node):
        pass

    @abstractmethod
    def switch_traffic(self, node):
        pass
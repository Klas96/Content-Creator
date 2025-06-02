from abc import ABC, abstractmethod

class ContentGenerator(ABC):
    def __init__(self, config: dict = None):
        self.config = config or {}
        self.status = "pending"
        self.output = None

    @abstractmethod
    async def generate(self, **kwargs):
        # kwargs will hold specific parameters like topic, style, etc.
        pass

    @abstractmethod
    def get_status(self) -> str:
        pass

    @abstractmethod
    def get_output(self):
        # Could return a file path, a URL, or raw content
        pass

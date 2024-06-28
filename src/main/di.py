from dishka import Provider, provide, Scope
from vkbottle import API

from src.config import Config


class DishkaProvider(Provider):
    def __init__(self, api: API, config: Config) -> None:
        self.api = api
        self.config = config
        super().__init__()

    @provide(scope=Scope.APP)
    async def get_api(self) -> API:
        return self.api

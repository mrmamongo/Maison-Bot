import asyncio
import os
from threading import Thread

import anyio
import uvicorn
from dishka import make_async_container
from dishka.integrations.fastapi import setup_dishka as setup_dishka_fastapi
from fastapi import FastAPI
from loguru import logger
from vkbottle import API, Bot
from vkbottle.framework.labeler import BotLabeler

from src.config import Config, get_config
from src.infra.loguru import setup_logging
from src.main.di import DishkaProvider
from src.presentation.di import DishkaMessageView
from src.presentation.vk import setup_vk
from src.presentation.web import setup_fastapi

config: Config = get_config()
setup_logging(config.logging)


def construct_lifespan(api: API, labeler: BotLabeler):
    async def lifespan(app: FastAPI):
        bot = Bot(api=api, labeler=labeler)
        Thread(target=asyncio.run, args=(bot.run_polling(),), daemon=True).start()
        logger.info("Stared bot in lifespan")

        yield {"bot": bot}

    return lifespan


def get_app() -> FastAPI:
    logger.info("Initializing vkbottle")
    api = API(token=config.vk.token)

    container = make_async_container(DishkaProvider(config=config, api=api))
    labeler = BotLabeler(message_view=DishkaMessageView(container))
    setup_vk(labeler)
    logger.info("Initializing fastapi")
    fastapi = setup_fastapi(config.api, lifespan=construct_lifespan(api, labeler))
    logger.info("Starting service")

    setup_dishka_fastapi(container, fastapi)

    return fastapi


async def run() -> None:
    app = get_app()
    server = uvicorn.Server(
        config=uvicorn.Config(
            app=app,
            host=config.api.host,
            port=config.api.port,
            workers=config.api.workers,
            reload_dirs=config.api.reload_dirs,
        )
    )
    server.config.setup_event_loop()
    await server.serve()


def main() -> None:
    try:
        anyio.run(run)
        exit(os.EX_OK)
    except SystemExit:
        exit(os.EX_OK)
    except Exception:
        logger.exception("Unexpected error occurred")
        exit(1)


if __name__ == "__main__":
    main()

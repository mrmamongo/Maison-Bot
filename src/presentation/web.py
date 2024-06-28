from dishka.integrations.fastapi import DishkaRoute
from fastapi import APIRouter

from typing import TypeVar

from fastapi import FastAPI
from loguru import logger
from starlette import status
from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from src.application.errors import BaseError, BaseErrorGroup
from src.config import ApiConfig

TError = TypeVar("TError", bound=BaseError)


def make_exception_handler(ex_type: type[TError]):
    async def exception_handler(request: Request, exc: TError) -> JSONResponse:
        logger.exception(exc)
        return JSONResponse(
            status_code=exc.status_code,
            content={"errors": [str(exc)]},
        )

    return exception_handler


async def exception_group_handler(
    request: Request, exc: BaseErrorGroup
) -> JSONResponse:
    logger.error("Some errors...", errors=exc.exceptions)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"errors": [str(exc) for exc in exc.exceptions]},
    )


def setup_exception_handlers(app: FastAPI) -> None:
    for exc_type in [
        BaseError,
    ]:
        app.exception_handler(exc_type)(make_exception_handler(exc_type))

    app.exception_handler(BaseErrorGroup)(exception_group_handler)


def setup_fastapi(config: ApiConfig, lifespan) -> FastAPI:
    app = FastAPI(lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=config.cors_origins,
        allow_credentials=config.allow_credentials,
        allow_methods=config.allow_methods,
        allow_headers=config.allow_headers,
    )

    router = APIRouter(prefix="/api", route_class=DishkaRoute)

    app.include_router(router)
    setup_exception_handlers(app)

    return app

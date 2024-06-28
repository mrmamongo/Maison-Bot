from typing import Callable, List

from dishka import AsyncContainer
from dishka.integrations.base import wrap_injection
from vkbottle import API, ABCHandler, ABCStateDispenser
from vkbottle.dispatch.views.bot import BotMessageView
from vkbottle.modules import logger
from vkbottle.tools.dev.mini_types.bot import message_min, MessageMin

CONTAINER_NAME = "__dishka_container__"
DEFAULT_STATE_KEY = "peer_id"


class DishkaMessageView(BotMessageView):
    handlers: list[ABCHandler]
    state_source_key: str
    default_text_approximators: List[Callable[[MessageMin], str]]
    replace_mention = False

    def __init__(self, container: AsyncContainer):
        super().__init__()
        self.state_source_key = DEFAULT_STATE_KEY
        self.default_text_approximators = []
        self.container = container

    @staticmethod
    def get_event_type(event: dict) -> str:
        return event["type"]

    @staticmethod
    async def get_message(
        event: dict, ctx_api: API, replace_mention: bool
    ) -> MessageMin:
        return message_min(event, ctx_api, replace_mention)

    async def handle_event(
        self, event: MessageMin, ctx_api: API, state_dispenser: ABCStateDispenser
    ) -> None:
        # For user event mapping, consider checking out
        # https://dev.vk.com/api/user-long-poll/getting-started
        logger.debug(
            "Handling event ({}) with message view", self.get_event_type(event)
        )
        context_variables: dict = {}
        message = await self.get_message(event, ctx_api, self.replace_mention)
        message.state_peer = await state_dispenser.cast(self.get_state_key(message))

        for text_ax in self.default_text_approximators:
            message.text = text_ax(message)

        mw_instances = await self.pre_middleware(message, context_variables)
        if mw_instances is None:
            logger.info("Handling stopped, pre_middleware returned error")
            return

        handle_responses = []
        handlers = []

        for handler in self.handlers:
            result = await handler.filter(message)
            logger.debug("Handler {} returned {}", handler, result)

            if result is False:
                continue

            elif isinstance(result, dict):
                context_variables.update(result)

            handler_response = await wrap_injection(
                func=handler.handler,
                is_async=True,
                container_getter=lambda _, __: self.container,
            )(message, **context_variables)
            handle_responses.append(handler_response)
            handlers.append(handler)

            return_handler = self.handler_return_manager.get_handler(handler_response)
            if return_handler is not None:
                await return_handler(
                    self.handler_return_manager,
                    handler_response,
                    message,
                    context_variables,
                )

            if handler.blocking:
                break

        await self.post_middleware(mw_instances, handle_responses, handlers)

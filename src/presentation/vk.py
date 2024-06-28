from dishka import FromDishka
from loguru import logger
from vkbottle import API
from vkbottle.bot import Message
from vkbottle.dispatch.rules.base import PeerRule
from vkbottle.framework.labeler import BotLabeler
from vkbottle_types.events import GroupEventType

labeller = BotLabeler()


def setup_vk(main_labeller: BotLabeler) -> None:
    main_labeller.load(labeller)


@labeller.raw_event(
    GroupEventType.GROUP_JOIN,
)
async def on_group_join(message: Message) -> None:
    await message.answer(
        "Всем привет! Добавьте меня в администраторы чата, чтобы я мог видеть всю историю"
    )


@labeller.chat_message(PeerRule(from_chat=True))
async def on_message(message: Message, api: FromDishka[API]) -> None:
    users_info = await api.users.get(message.from_id)
    logger.info(users_info[0].nickname)
    await message.answer("Привет, {}".format((await message.get_user()).first_name))

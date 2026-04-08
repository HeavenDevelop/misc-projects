from aiogram import BaseMiddleware
from aiogram.types import Message, TelegramObject, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.enums import ChatMemberStatus
from typing import Any, Awaitable, Callable, Dict

class BasicMid(BaseMiddleware):
    def __init__(self, channelId: int):
        self.channelId = channelId

    async def __call__(self, handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]], event: Message, data: Dict[str, Any]) -> Any:
        bot = data["bot"]
        if not event.from_user:
            return await handler(event, data)
            
        userId = event.from_user.id
        try:
            member = await bot.get_chat_member(chat_id=self.channelId, user_id=userId)
            if member.status in [
                ChatMemberStatus.MEMBER,
                ChatMemberStatus.ADMINISTRATOR,
                ChatMemberStatus.CREATOR,
                ChatMemberStatus.RESTRICTED
            ]:
                return await handler(event, data)
            else:
                payload = ""
                if event.text and event.text.startswith("/start "):
                    payload = event.text.split(" ")[1]
                cb_data = f"check_sub|{payload}" if payload else "check_sub|"

                inlineKb = InlineKeyboardMarkup(
                    inline_keyboard=[
                        [InlineKeyboardButton(text="Основной канал", url="https://t.me/buyblackpepe")],
                        [InlineKeyboardButton(text="Проверить подписку ✅", callback_data=cb_data)]
                    ]
                )
                await event.answer("Перед использованием бота подпишитесь на наши каналы:", reply_markup=inlineKb)
                return
        except Exception as e:
            print(f"Middleware Error: {e}") 
            return await handler(event, data)


import asyncio
from aiogram import Bot, Dispatcher, F
from aiogram.utils.deep_linking import create_start_link, decode_payload
from aiogram.filters import Command, CommandStart, CommandObject
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncAttrs
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import String, select, update, delete, BigInteger
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from mid import *

from aiogram.client.session.aiohttp import AiohttpSession

session = AiohttpSession(proxy="http://proxy.server:3128")
bot = Bot(token="", session=session)
dp = Dispatcher()

engine = create_async_engine("sqlite+aiosqlite:///./data.db")
session = async_sessionmaker(engine, expire_on_commit=False)

class Base(AsyncAttrs, DeclarativeBase):
    pass

class User(Base):
    __tablename__ = "users"
    userId: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    referralCount: Mapped[int]
    starsBalance: Mapped[int]
    ref: Mapped[bool]

async def initDb():
    async with engine.begin() as connect:
        await connect.run_sync(Base.metadata.create_all)

async def newUser(id: int):
    async with session() as ses:
        user = User(userId=id, referralCount=0, starsBalance=0, ref=False)
        ses.add(user)
        await ses.commit()

async def getUserData(id: int):
    async with session() as ses:
        user = await ses.get(User, id)
        if not user:
            await newUser(id)
            user = await ses.get(User, id)
        return user

async def addUserBalance(id: int, amount: int):
    async with session() as ses:
        user = await getUserData(id)
        req = update(User).where(User.userId == id).values(starsBalance=(user.starsBalance+amount))
        await ses.execute(req)
        await ses.commit()

async def deleteUser(id: int):
    async with session() as ses:
        req = delete(User).where(User.userId == id)
        await ses.execute(req)
        await ses.commit()

async def addOneRef(id: int, fromId: int):
    async with session() as ses:
        user = await getUserData(fromId)
        if not user.ref:
            user = await getUserData(id)
            req = update(User).where(User.userId == id).values(referralCount=(user.referralCount+1), starsBalance=(user.starsBalance+3))
            req2 = update(User).where(User.userId == fromId).values(ref=True)
            await ses.execute(req)
            await ses.execute(req2)
            await ses.commit()
        return

async def createRef(id: int):
    return await create_start_link(bot, str(id))

async def startMenu(event: Message | CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Мой профиль", callback_data="profile")],
        [InlineKeyboardButton(text="Реферальная система", callback_data="referral")],
        [InlineKeyboardButton(text="Вывести звезды", callback_data="withdraw")]])
    text = "Добро пожаловать в бота для <b>заработка звезд</b>!\nПриглашайте друзей в бота и получайте звезды на свой баланс.\nНажмите на одну из кнопок ниже для продолжения:\n"
    if isinstance(event, Message):
        await event.answer(text, reply_markup=kb, parse_mode="HTML")
    elif isinstance(event, CallbackQuery):
        await event.answer()
        await event.message.edit_text(text, reply_markup=kb, parse_mode="HTML")

@dp.message(CommandStart())
async def start(message: Message, command: CommandObject):
    user = await getUserData(message.from_user.id)
    args = command.args
    if args and not user.ref:
        try:
            refId = int(args)
            if refId != message.from_user.id:
                await addOneRef(refId, message.from_user.id)
        except Exception:
            pass
    await startMenu(message)

@dp.callback_query(F.data == "profile")
async def profile(call: CallbackQuery):
    await call.answer()
    user = await getUserData(call.from_user.id)
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Назад", callback_data="back")]])
    await call.message.edit_text(f"Имя: {call.from_user.first_name}\nID: <code>{call.from_user.id}</code>\nБаланс звезд: {user.starsBalance} | {user.referralCount} реф.", reply_markup=kb, parse_mode="HTML")

@dp.callback_query(F.data == "referral")
async def profile(call: CallbackQuery):
    await call.answer()
    user = await getUserData(call.from_user.id)
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Назад", callback_data="back")]])
    await call.message.edit_text(f"Вот ваша реферальная ссылка:\n<code>{await createRef(user.userId)}</code>\nКаждый реферал дает вам +3 звезды на баланс!", reply_markup=kb, parse_mode="HTML")

@dp.callback_query(F.data == "withdraw")
async def withdrawMenu(call: CallbackQuery):
    await call.answer()
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="25", callback_data="stars_25"), InlineKeyboardButton(text="50", callback_data="stars_50")],
        [InlineKeyboardButton(text="75", callback_data="stars_75"), InlineKeyboardButton(text="100", callback_data="stars_100")],
        [InlineKeyboardButton(text="Назад", callback_data="back")],])
    await call.message.edit_text("Выберите сумму для вывода:", reply_markup=kb)

@dp.callback_query(F.data == "back")
async def back(call: CallbackQuery):
    await call.answer()
    await startMenu(call)


@dp.callback_query(F.data.startswith("check_sub|"))
async def checkSubHandler(call: CallbackQuery, bot: Bot):
    channelId = -1003531060152
    payload = call.data.split("|")[1]

    try:
        member = await bot.get_chat_member(chat_id=channelId, user_id=call.from_user.id)

        if member.status in ['member', 'administrator', 'creator', 'restricted']:
            await call.message.delete()
            await getUserData(call.from_user.id)

            if payload:
                try:
                    refId = int(payload)
                    if refId != call.from_user.id:
                        await addOneRef(refId, call.from_user.id)
                except Exception:
                    pass

            await call.message.answer("Спасибо за подписку! Добро пожаловать!\nНапишите /start чтобы продолжить")
        else:
            await call.answer("Вы еще не подписались на канал!", show_alert=True)

    except Exception as e:
        await call.answer("Произошла ошибка при проверке.", show_alert=True)
        
@dp.callback_query(F.data.startswith("stars_"))
async def stars(call: CallbackQuery):
    await call.answer()
    dataParts = call.data.split("_")
    amount = int(dataParts[1])
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Подтвердить", callback_data=f"withdraw_{amount}")],
        [InlineKeyboardButton(text="Отмена", callback_data="back")]])
    await call.message.edit_text(f"Подтвердите покупку {amount} звезд:", reply_markup=kb)

@dp.callback_query(F.data.startswith("withdraw_"))
async def withdraw(call: CallbackQuery):
    await call.answer()
    dataParts = call.data.split("_")
    amount = int(dataParts[1])
    user = await getUserData(call.from_user.id)
    if user.starsBalance >= amount:
        await addUserBalance(user.userId, (amount*-1))
        await call.message.edit_text("Успешная оплата! Ожидате поступления звезд к вам на аккаунт\nДля продолжения нажмите /start")
    else:
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Назад", callback_data="back")]])
        await call.message.edit_text("Недостаточно звезд на балансе!", reply_markup=kb)


async def main():
    await initDb()
    dp.message.middleware(BasicMid(-1003531060152))
    await dp.start_polling(bot)

if __name__ == "__main__":
    print(111)
    asyncio.run(main())

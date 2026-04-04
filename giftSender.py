import asyncio
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command, CommandStart, StateFilter 
from aiogram.types import Message, LabeledPrice, PreCheckoutQuery, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, LabeledPrice, PreCheckoutQuery, Message
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State

buttons = {
    "5956217000635139069": "5379850840691476775",
    "5866352046986232958": "5289761157173775507",
    "5800655655995968830": "5226661632259691727",
    "5935895822435615975": "5359736160224586485",
    "5893356958802511476": "5317000922096769303",
    "5922558454332916696": "5345935030143196497",
    "5801108895304779062": "5224628072619216265",
    "5170145012310081615": "5283228279988309088",
    "5170233102089322756": "5280598054901145762",
    "5170250947678437525": "5280615440928758599",
    "5168103777563050263": "5280947338821524402",
    "5170144170496491616": "5280659198055572187",
    "5170314324215857265": "5280774333243873175",
    "5170564780938756245": "5283080528818360566",
    "6028601630662853006": "5451905784734574339",
    "5168043875654172773": "5280769763398671636",
    "5170690322832818290": "5280651583078556009",
    "5170521118301225164": "5280922999241859582",
}

class GiftForm(StatesGroup):
    giftText = State()

def getKb(data: dict):
    builder = InlineKeyboardBuilder()
    for data, id in data.items():
        builder.add(InlineKeyboardButton(
                text=" ",
                callback_data=data,
                icon_custom_emoji_id=id))
    builder.adjust(3)
    return builder.as_markup()

dp = Dispatcher()
bot = Bot(token="")

@dp.message(CommandStart())
async def start(message: Message):
    kb = getKb(buttons)
    await message.answer("Выберите подарок для покупки\nSelect a gift to purchase:", reply_markup=kb)

@dp.callback_query()
async def callback(call: CallbackQuery, state: FSMContext):
    await call.answer()
    await call.message.edit_text("Введите комментарий к подарку или - если без\nEnter a comment for the gift or - if without:")
    await state.update_data(callback=call.data)
    await state.set_state(GiftForm.giftText)

@dp.message(StateFilter(GiftForm.giftText))
async def processGift(message: Message, state: FSMContext):
    data = await state.get_data()
    giftId = int(data.get("callback"))
    giftComment = message.text
    await state.update_data(comment=message.text)
    amount = 0
    match giftId:
        case 5170233102089322756 | 5170145012310081615: 
            amount = 15
        case 5170250947678437525 | 5168103777563050263: 
            amount = 25
        case 5170144170496491616 | 5170314324215857265 | 5170564780938756245 | 6028601630662853006:
            amount = 50
        case 5168043875654172773 | 5170690322832818290 | 5170521118301225164:
            amount = 100
        case _ if giftId in [5800655655995968830, 5922558454332916696, 5956217000635139069, 5935895822435615975, 5893356958802511476, 5801108895304779062, 5866352046986232958]:
            amount = 50
    await message.answer_invoice(
        title="Gift",
        description=f"Оплатите чек для получения подарка | Pay the check to receive the gift:",
        payload=f"{giftId}", 
        provider_token="",
        currency="XTR",
        prices=[LabeledPrice(label="Gift", amount=amount)])

@dp.pre_checkout_query()
async def preCheckout(preCheckoutQuery: PreCheckoutQuery):
    await preCheckoutQuery.answer(ok=True)

@dp.message(F.successful_payment)
async def payment(message: Message):
    payment = message.successful_payment
    giftId = payment.invoice_payload
    data = await state.get_data()
    giftComment = data.get("comment")
    if giftComment == "-":
        giftComment = ""
    try:
        await bot.send_gift(user_id=message.from_user.id, gift_id=giftId, text=giftComment)
    except Exception as e:
        await message.answer(e)
    await state.clear()


async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    print(111)
    asyncio.run(main())

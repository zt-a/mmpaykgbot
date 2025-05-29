import asyncio
import logging
import dotenv import load_dotenv
import os
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import (
    FSInputFile,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)

load_dotenv()
TOKEN = os.getenv('TOKEN')
ADMIN_ID = os.getenv('ADMIN_ID')
SUPPORT = os.getenv('SUPPORT')
MAX_AMOUNT = os.getenv('MAX_AMOUNT')
MIN_AMOUNT = os.getenv('MIN_AMOUNT')

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)
logger = logging.getLogger(__name__)

bot = Bot(token=TOKEN)
dp = Dispatcher(storage=MemoryStorage())

menu = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="📥 Пополнить"),
            KeyboardButton(text="📤 Вывести"),
        ],
        [
            KeyboardButton(text="❌ Отменить"),
            KeyboardButton(text="🏠 Главное меню"),
        ],
    ],
    resize_keyboard=True,
)


class DepositStates(StatesGroup):
    waiting_for_account = State()
    waiting_for_amount = State()
    waiting_for_receipt = State()


class WithdrawStates(StatesGroup):
    waiting_for_account = State()
    waiting_for_amount = State()
    waiting_for_requisites = State()
    waiting_for_code = State()


@dp.message(CommandStart())
async def start(message: types.Message):
    logger.info(f"User {message.from_user.id} started the bot.")
    await message.answer(
        "<b>👋 Добро пожаловать в <u>Mm Pay</u>!</b>\n\n"
        "💼 <i>У нас вы можете легко пополнить или вывести средства.</i>\n\n"
        "🔽 <b>Выберите действие ниже</b> — просто нажмите на кнопку 👇\n\n"
        '🛟 Поддержка: <a href="https://t.me/Mm_paysupport">@Mm_paysupport</a>',
        reply_markup=menu,
        parse_mode="HTML",
    )


@dp.message(F.text == "❌ Отменить")
@dp.message(Command("cancel"))
async def cancel(message: types.Message, state: FSMContext):
    logger.info(f"User {message.from_user.id} canceled an action.")
    await state.clear()
    await message.answer(
        "❌ <b>Действие отменено.</b>", parse_mode="HTML", reply_markup=menu
    )


@dp.message(F.text == "🏠 Главное меню")
@dp.message(Command("menu"))
async def main_menu(message: types.Message, state: FSMContext):
    logger.info(f"User {message.from_user.id} returned to main menu.")
    await state.clear()
    await message.answer(
        "<b>🏠 Добро пожаловать в <u>Главное меню</u></b>\n\n"
        "📲 Выберите одно из действий ниже, нажав на кнопку ⬇️\n\n"
        '🛟 Поддержка: <a href="https://t.me/Mm_paysupport">@Mm_paysupport</a>',
        reply_markup=menu,
        parse_mode="HTML",
    )


# ====================
# Пополнение
# ====================
@dp.message(F.text == "📥 Пополнить")
@dp.message(Command("replenish"))
async def deposit_start(message: types.Message, state: FSMContext):
    logger.info(f"User {message.from_user.id} started deposit process.")
    caption = (
        "<b>📥 <u>Пополнение счёта</u></b>\n\n"
        "💳 Пожалуйста, введите <b>номер счёта</b> или <b>ID</b>, на который вы хотите пополнить баланс.\n\n"
        "📌 Убедитесь в правильности данных перед продолжением."
    )
    try:
        photo = FSInputFile("img/login_img.jpg")
        await message.answer_photo(
            photo=photo, caption=caption, parse_mode="HTML"
        )
    except FileNotFoundError:
        logger.warning("Image img/login_img.jpg not found.")
        await message.answer(caption, parse_mode="HTML")
    await state.set_state(DepositStates.waiting_for_account)


@dp.message(DepositStates.waiting_for_account)
async def deposit_account(message: types.Message, state: FSMContext):
    logger.info(
        f"User {message.from_user.id} entered deposit account: {message.text}"
    )
    await state.update_data(account=message.text)
    await message.answer(
        f"💸 <b>Введите сумму для пополнения (от {MIN_AMOUNT} до {MAX_AMOUNT} сом):</b>",
        parse_mode="HTML",
    )
    await state.set_state(DepositStates.waiting_for_amount)


@dp.message(DepositStates.waiting_for_amount)
async def deposit_amount(message: types.Message, state: FSMContext):
    if not message.text.isdigit() or int(message.text) <= 0 or int(message.text) < {MIN_AMOUNT} or int(message.text) > {MAX_AMOUNT}:
        logger.warning(
            f"User {message.from_user.id} entered invalid deposit amount: {message.text}"
        )
        await message.answer(
            f"⚠️ Введите корректную сумму (число больше чем {MIN_AMOUNT} и меньше чем {MAX_AMOUNT}).", parse_mode="HTML"
        )
        return
    await state.update_data(amount=message.text)
    data = await state.get_data()
    logger.info(
        f"User {message.from_user.id} entered deposit amount: {data['amount']}"
    )
    amount = int(data["amount"])
    amount = amount * 100
    amount_w = f"{len(str(amount))}{amount}"
    caption = (
        "<b>📲 Реквизиты для оплаты</b>\n\n"
        "📞 <b>Телефон:</b> +996 <code>779588011</code>\n\n"
        "🔗 <b>Ссылка для оплаты через Mbank:</b>\n"
        f"<a href='https://app.mbank.kg/qr/#00020101021132500012c2c.mbank.kg0102021012996779588011120211130211520499995303417540{amount_w}5908BELEK%20T.6304646a'>"
        "💳 Перейти к оплате</a>"
    )

    try:
        photo = FSInputFile("img/qr_codes/mbank_qr.jpg")
        await message.answer_photo(
            photo=photo, caption=caption, parse_mode="HTML"
        )
    except FileNotFoundError:
        logger.warning("Image img/qr_codes/mbank_qr.jpg not found.")
        await message.answer(caption, parse_mode="HTML")
    await message.answer(
        "📷<b>Пожалуйста, отправьте скриншот или фото чека:</b>",
        parse_mode="HTML",
    )
    await state.set_state(DepositStates.waiting_for_receipt)


@dp.message(DepositStates.waiting_for_receipt, F.photo)
async def deposit_receipt(message: types.Message, state: FSMContext):
    data = await state.get_data()
    photo_id = message.photo[-1].file_id
    logger.info(f"User {message.from_user.id} sent deposit receipt.")

    inline_kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Подтвердить",
                    callback_data=f"approve_deposit:{message.from_user.id}",
                ),
                InlineKeyboardButton(
                    text="❌ Отклонить",
                    callback_data=f"decline_deposit:{message.from_user.id}",
                ),
            ]
        ]
    )

    text = (
        f"<b>📥 Новая заявка на пополнение</b>\n\n"
        f"👤 <b>Пользователь:</b> @{message.from_user.username or message.from_user.full_name} (ID: <code>{message.from_user.id}</code>)\n"
        f"🧾 <b>Счёт/ID:</b> <code>{data.get('account')}</code>\n"
        f"💰 <b>Сумма:</b> {data.get('amount')} сом\n"
        f"📌 <b>Заявка №{data.get('account')}</b>\n\n"
        f"🔍 Проверьте чек и подтвердите вручную."
    )

    await bot.send_message(
        chat_id=ADMIN_ID,
        text=text + "\n\nОжидание....",
        parse_mode="HTML",
        reply_markup=None,
    )
    await bot.send_photo(
        chat_id=ADMIN_ID,
        photo=photo_id,
        caption=text,
        parse_mode="HTML",
        reply_markup=inline_kb,
    )
    await message.answer(
        "✅ <b>Заявка отправлена администратору!</b>\n⏳ Ожидайте подтверждения.\n🛟 SUPPORT: "
        + SUPPORT,
        parse_mode="HTML",
    )
    await state.clear()


@dp.callback_query(F.data.startswith("approve_deposit:"))
async def approve_deposit(call: types.CallbackQuery):
    user_id = int(call.data.split(":")[1])
    logger.info(f"Admin approved deposit for user {user_id}.")
    try:
        await bot.send_message(
            chat_id=user_id,
            text="✅ <b>Ваша заявка на пополнение подтверждена!</b>",
            parse_mode="HTML",
        )
        await bot.send_message(
            chat_id=ADMIN_ID,
            text="✅ <b>Заявка на пополнение подтверждена!</b>",
            parse_mode="HTML",
        )
        # Работаем с caption и edit_caption
        caption = call.message.caption or ""
        await call.message.edit_caption(
            caption + "\n\n✅ <b>Заявка подтверждена.</b>",
            parse_mode="HTML",
            reply_markup=None,
        )
        await call.answer("Заявка подтверждена ✅")
    except Exception as e:
        logger.error(f"Error sending deposit approval message: {e}")
        await call.answer(
            f"Ошибка при отправке подтверждения: {e}", show_alert=True
        )


@dp.callback_query(F.data.startswith("decline_deposit:"))
async def decline_deposit(call: types.CallbackQuery):
    user_id = int(call.data.split(":")[1])
    logger.info(f"Admin declined deposit for user {user_id}.")
    try:
        await bot.send_message(
            chat_id=user_id,
            text="❌ <b>Ваша заявка на пополнение отклонена.</b>",
            parse_mode="HTML",
        )
        await bot.send_message(
            chat_id=ADMIN_ID,
            text="❌ <b>Заявка на пополнение отклонена.</b>",
            parse_mode="HTML",
        )
        caption = call.message.caption or ""
        await call.message.edit_caption(
            caption + "\n\n❌ <b>Заявка отклонена.</b>",
            parse_mode="HTML",
            reply_markup=None,
        )
        await call.answer("Заявка отклонена ❌")
    except Exception as e:
        logger.error(f"Error sending deposit decline message: {e}")
        await call.answer(f"Ошибка при отправке отказа: {e}", show_alert=True)


# ====================
# Вывод
# ====================
@dp.message(F.text == "📤 Вывести")
@dp.message(Command("withdraw"))
async def withdraw_start(message: types.Message, state: FSMContext):
    logger.info(f"User {message.from_user.id} started withdraw process.")
    caption = (
        "<b>📤 Заявка на вывод средств</b>\n\n"
        "🔐 Пожалуйста, введите номер счёта или ID, из который хотите вывести средства."
    )
    try:
        photo = FSInputFile("img/login_img.jpg")
        await message.answer_photo(
            photo=photo, caption=caption, parse_mode="HTML"
        )
    except FileNotFoundError:
        logger.warning("Image img/login_img.jpg not found.")
        await message.answer(caption, parse_mode="HTML")
    await state.set_state(WithdrawStates.waiting_for_account)


@dp.message(WithdrawStates.waiting_for_account)
async def withdraw_account(message: types.Message, state: FSMContext):
    logger.info(
        f"User {message.from_user.id} entered withdraw account: {message.text}"
    )
    await state.update_data(account=message.text)
    await message.answer(
        "💸 <b>Введите сумму для вывода (от 150 до {MAX_AMOUNT} сом):</b>",
        parse_mode="HTML",
    )
    await state.set_state(WithdrawStates.waiting_for_amount)


@dp.message(WithdrawStates.waiting_for_amount)
async def withdraw_amount(message: types.Message, state: FSMContext):
    if not message.text.isdigit():
        logger.warning(
            f"User {message.from_user.id} entered invalid withdraw amount: {message.text}"
        )
        await message.answer(
            "⚠️ Введите корректное число для суммы.", parse_mode="HTML"
        )
        return
    amount = int(message.text)
    if amount < 50 or amount > 45000:
        logger.warning(
            f"User {message.from_user.id} entered withdraw amount out of range: {amount}"
        )
        await message.answer(
            "⚠️ Сумма должна быть от 50 до 45000 сом.", parse_mode="HTML"
        )
        return
    await state.update_data(amount=message.text)
    logger.info(
        f"User {message.from_user.id} entered withdraw amount: {amount}"
    )
    await message.answer(
        "💳 <b>Пожалуйста, введите ваши реквизиты для вывода (номер карты, счёта и т.д.):</b>\n"
        "📌 Убедитесь в правильности данных перед продолжением.\n"
        "📌 Образец: +996702388466 мбанк",
        parse_mode="HTML",
    )
    await state.set_state(WithdrawStates.waiting_for_requisites)


@dp.message(WithdrawStates.waiting_for_requisites)
async def withdraw_requisites(message: types.Message, state: FSMContext):
    logger.info(
        f"User {message.from_user.id} entered withdraw requisites: {message.text}"
    )
    await state.update_data(requisites=message.text)

    await message.answer(
        f"""<b>📤 Инструкция по выводу:</b>\n
📍Заходим👇
    📍1. Настройки!
    📍2. Вывести со счета!
    📍3. Наличные
    📍4. Сумму для Вывода!
Город: Баткен
Улица: Mm Pay (24/7)
    📍5. Подтвердить
    📍6. Получить Код!
    📍7. Отправить его нам
Если возникли проблемы 👇
💻 Оператор: {SUPPORT}
        """,
        parse_mode="HTML",
    )

    await message.answer("💳 Введите код: ")
    await state.set_state(WithdrawStates.waiting_for_code)


@dp.message(WithdrawStates.waiting_for_code)
async def withdraw_code(message: types.Message, state: FSMContext):
    await state.update_data(code=message.text)
    data = await state.get_data()

    inline_kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Подтвердить",
                    callback_data=f"approve_withdraw:{message.from_user.id}",
                ),
                InlineKeyboardButton(
                    text="❌ Отклонить",
                    callback_data=f"decline_withdraw:{message.from_user.id}",
                ),
            ]
        ]
    )

    text = (
        f"<b>📤 Новая заявка на вывод</b>\n\n"
        f"👤 <b>Пользователь:</b> @{message.from_user.username or message.from_user.full_name} (ID: <code>{message.from_user.id}</code>)\n"
        f"🧾 <b>Счёт/ID:</b> <code>{data.get('account')}</code>\n"
        f"✅ <b>Код подтверждение:</b> {data.get('code')}\n"
        f"💰 <b>Сумма:</b> {data.get('amount')} сом\n"
        f"📌 <b>Реквизиты:</b> {data.get('requisites')}\n\n"
        f"🔍 Проверьте код и подтвердите вручную."
    )

    await bot.send_message(
        chat_id=ADMIN_ID, text=text, parse_mode="HTML", reply_markup=inline_kb
    )

    await message.answer(
        "✅ <b>Заявка отправлена администратору!</b>\n⏳ Ожидайте подтверждения.\n🛟 SUPPORT: "
        + SUPPORT,
        parse_mode="HTML",
    )
    await state.clear()


@dp.callback_query(F.data.startswith("approve_withdraw:"))
async def approve_withdraw(call: types.CallbackQuery):
    user_id = int(call.data.split(":")[1])
    logger.info(f"Admin approved withdraw for user {user_id}.")

    if (
        "Заявка подтверждена" in call.message.text
        or "Заявка отклонена" in call.message.text
    ):
        await call.answer("Заявка уже обработана.", show_alert=True)
        return

    try:
        await bot.send_message(
            chat_id=user_id,
            text="✅ <b>Ваша заявка на вывод подтверждена!</b>",
            parse_mode="HTML",
        )
        await call.message.edit_text(
            call.message.text + "\n\n✅ <b>Заявка подтверждена.</b>",
            parse_mode="HTML",
            reply_markup=None,
        )
        await call.answer("Заявка подтверждена ✅")
    except Exception as e:
        logger.error(f"Error sending withdraw approval message: {e}")
        await call.answer(f"Ошибка: {e}", show_alert=True)


@dp.callback_query(F.data.startswith("decline_withdraw:"))
async def decline_withdraw(call: types.CallbackQuery):
    user_id = int(call.data.split(":")[1])
    logger.info(f"Admin declined withdraw for user {user_id}.")

    if (
        "Заявка подтверждена" in call.message.text
        or "Заявка отклонена" in call.message.text
    ):
        await call.answer("Заявка уже обработана.", show_alert=True)
        return

    try:
        await bot.send_message(
            chat_id=user_id,
            text="❌ <b>Ваша заявка на вывод отклонена.</b>",
            parse_mode="HTML",
        )
        await call.message.edit_text(
            call.message.text + "\n\n❌ <b>Заявка отклонена.</b>",
            parse_mode="HTML",
            reply_markup=None,
        )
        await call.answer("Заявка отклонена ❌")
    except Exception as e:
        logger.error(f"Error sending withdraw decline message: {e}")
        await call.answer(f"Ошибка: {e}", show_alert=True)



if __name__ == "__main__":
    logger.info("Bot started")
    asyncio.run(dp.start_polling(bot))

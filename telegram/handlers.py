from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import (
    Message,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)

from modules.agent import get_agent_response
from modules.middleware.order_confirmation import HITLManager
from .hitl import set_pending_order


router = Router()


@router.message(CommandStart())
async def start_handler(message: Message):

    await message.answer(
        "🍕 Привет!\n"
        "Я AI-помощник по заказу пиццы.\n\n"
        "Что хотите заказать?"
    )


@router.message()
async def message_handler(message: Message):

    if not message.text:
        return

    user_id = message.from_user.id

    try:

        response = get_agent_response(
            message=message.text,
            user_id=user_id,
        )

        # Агент запросил подтверждение
        if response.get("__interrupt__"):

            action = HITLManager.get_order_from_interrupt(
                response
            )

            if action is None:
                await message.answer(
                    "Не удалось получить данные заказа."
                )
                return

            order = action.get("args", {})

            set_pending_order(
                user_id=user_id,
                config={
                    "configurable": {
                        "user_id": user_id,
                        "thread_id": f"user:{user_id}",
                    }
                },
                order=order,
            )

            await send_order_confirmation(
                message=message,
                order=order,
            )

            return

        answer = response[
            "messages"
        ][-1].content

        await message.answer(answer)

    except Exception as e:

        print(
            f"Ошибка Telegram "
            f"user_id={user_id}: {e}"
        )

        await message.answer(
            "Произошла ошибка при обработке запроса."
        )


async def send_order_confirmation(
    message: Message,
    order: dict,
):

    items = order.get("items", [])

    lines = [
        "🍕 <b>Проверьте заказ</b>",
        "",
    ]

    for item in items:

        name = item.get("name", "Неизвестная пицца")
        quantity = item.get("quantity", 0)
        price = item.get("price")
        subtotal = item.get("subtotal")

        if price is not None and subtotal is not None:

            lines.append(
                f"• {name} — "
                f"{quantity} шт. × "
                f"{price} ₽ = "
                f"{subtotal} ₽"
            )

        else:

            lines.append(
                f"• {name} — {quantity} шт."
            )

    total = order.get("total")
    address = order.get("address")

    lines.append("")

    if total is not None:
        lines.append(
            f"💰 <b>Итого:</b> {total} ₽"
        )

    if address:
        lines.append(
            f"📍 <b>Адрес:</b> {address}"
        )

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Подтвердить",
                    callback_data="order:approve",
                ),
                InlineKeyboardButton(
                    text="❌ Отменить",
                    callback_data="order:reject",
                ),
            ]
        ]
    )

    await message.answer(
        "\n".join(lines),
        reply_markup=keyboard,
        parse_mode="HTML",
    )
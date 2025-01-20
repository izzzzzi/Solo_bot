import random
from typing import Any

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder

from config import CAPTCHA_EMOJIS
from handlers.start import start_command
from logger import logger

router = Router()


async def generate_captcha(state: FSMContext):
    """Генерирует новую капчу и сохраняет правильный ответ в состоянии

    Пример словаря CAPTCHA_EMOJIS:
    {
        "🐶": "собаку",   # Собака
        "🐱": "кошку",    # Кошка
        "🐭": "мышь",     # Мышь
        "🐹": "хомяка",   # Хомяк
        "🐰": "кролика",  # Кролик
        ...
    }
    """
    # Выбираем случайный эмодзи и его описание из конфига
    correct_emoji, correct_text = random.choice(list(CAPTCHA_EMOJIS.items()))
    
    # Получаем 3 случайных неправильных эмодзи
    wrong_emojis = random.sample(
        [e for e in CAPTCHA_EMOJIS.keys() if e != correct_emoji], 3
    )
    
    # Создаем список всех эмодзи и перемешиваем их
    all_emojis = [correct_emoji] + wrong_emojis
    random.shuffle(all_emojis)
    
    # Сохраняем правильный ответ в состоянии
    await state.update_data(correct_emoji=correct_emoji)
    
    # Создаем клавиатуру
    builder = InlineKeyboardBuilder()
    for emoji in all_emojis:
        builder.button(text=emoji, callback_data=f"captcha_{emoji}")
    builder.adjust(2, 2)
    
    return {
        "text": f"🔒 Для подтверждения что вы не робот,\nвыберите кнопку с {correct_text}",
        "markup": builder.as_markup()
    }


@router.callback_query(F.data.startswith("captcha_"))
async def check_captcha(
    callback: CallbackQuery, state: FSMContext, session: Any, admin: bool
):
    """Проверяет ответ пользователя на капчу"""
    selected_emoji = callback.data.split("captcha_")[1]
    state_data = await state.get_data()
    correct_emoji = state_data.get("correct_emoji")

    if selected_emoji == correct_emoji:
        logger.info(f"Пользователь {callback.message.chat.id} успешно прошел капчу")
        await start_command(callback.message, state, session, admin)
    else:
        logger.warning(
            f"Пользователь {callback.message.chat.id} неверно ответил на капчу"
        )
        captcha = await generate_captcha(state)
        await callback.message.answer(
            text=captcha["text"], reply_markup=captcha["markup"]
        )
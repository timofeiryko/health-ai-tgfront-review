"""This module contains utility functions and classes used in the main bot.py module."""

from aiogram.filters.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from aiogram import Bot, Dispatcher

from flag import flag
from dotenv import load_dotenv

from typing import Callable
from datetime import datetime

from translated_messages import MESSAGES_DICT

load_dotenv()

SUPPORTED_LANGS = {
    'en': 'English',
    'ru': 'Русский',
    'es': 'Español',
}

class RegistrationStates(StatesGroup):

    language = State()
    profile_or_skip = State()

    birth_date = State()
    sex = State()
    mass = State()
    height = State()

    eats_meat = State()
    eats_fish = State()
    eats_dairy = State()
    description = State()

    completed = State()
    consulting = State()
    initial_consultation_completed = State()

    # change_language = State()
    # TODO: ANOTHER STATES GROUP FOR CHANGING SETTINGS?

def get_lang_keyboard() -> ReplyKeyboardMarkup:

    keyboard = []
    
    for unicode, lang in SUPPORTED_LANGS.items():
        unicode = 'gb' if unicode == 'en' else unicode
        keyboard.append(KeyboardButton(text=f'{flag(unicode)} {lang}'))

    return ReplyKeyboardMarkup(keyboard=[keyboard], resize_keyboard=True)

def get_sex_keyboard(preferred_lang: str) -> ReplyKeyboardMarkup:
    
    keyboard = []
    keyboard.append(KeyboardButton(text=MESSAGES_DICT['male'][preferred_lang]))
    keyboard.append(KeyboardButton(text=MESSAGES_DICT['female'][preferred_lang]))
    keyboard.append(KeyboardButton(text=MESSAGES_DICT['other'][preferred_lang]))
    
    return ReplyKeyboardMarkup(keyboard=[keyboard], resize_keyboard=True)

def get_mass_options_keyboard(preferred_lang: str) -> ReplyKeyboardMarkup:
    
    builder = ReplyKeyboardBuilder()
    
    options = [KeyboardButton(text=option) for option in [MESSAGES_DICT['mass_option_low'][preferred_lang], MESSAGES_DICT['mass_option_high'][preferred_lang]]]
    builder.row(*options)
        
    builder.row(KeyboardButton(text=MESSAGES_DICT['mass_option_average'][preferred_lang]))
    
    return builder.as_markup(resize_keyboard=True)

def get_height_options_keyboard(preferred_lang: str) -> ReplyKeyboardMarkup:
    
    builder = ReplyKeyboardBuilder()

    options = [KeyboardButton(text=option) for option in [MESSAGES_DICT['height_option_low'][preferred_lang], MESSAGES_DICT['height_option_high'][preferred_lang]]]
    builder.row(*options)
    
    builder.row(KeyboardButton(text=MESSAGES_DICT['height_option_average'][preferred_lang]))
    
    return builder.as_markup(resize_keyboard=True)

def get_consultation_markup(preferred_lang: str):
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text=MESSAGES_DICT['complete_consultation'][preferred_lang])
            ]
        ], resize_keyboard=True
    )

def check_extract_lang(message: Message):
    """Returns lang code if language can be saved, False if it's not supported"""

    supported_options = {}
    for unicode, lang in SUPPORTED_LANGS.items():
        lang_code = 'gb' if unicode == 'en' else unicode
        supported_options[f'{flag(lang_code)} {lang}'] = unicode

    if message.text in supported_options.keys():
        return supported_options[message.text]
    else:
        return False
    
# async eats_choice_handler, if the answer is not yes or no, asks again until the answer is yes or no
async def eats_choice_handler(message: Message, state: FSMContext, next_state: Callable, next_message_text: str, last=False) -> None:
    """This handler receives user's choice of eating habits"""

    data = await state.get_data()
    preferred_lang = data['preferred_lang']

    markup = ReplyKeyboardRemove() if last else ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text=MESSAGES_DICT['yes'][preferred_lang]),
            KeyboardButton(text=MESSAGES_DICT['no'][preferred_lang]),
        ]
    ], resize_keyboard=True
)


    if message.text == MESSAGES_DICT['yes'][preferred_lang]:
        await state.update_data(eats=True)
        await state.set_state(next_state)
        await message.answer(next_message_text, reply_markup=markup)

    elif message.text == MESSAGES_DICT['no'][preferred_lang]:
        await state.update_data(eats=False)
        await state.set_state(next_state)
        await message.answer(next_message_text, reply_markup=markup)
    else:
        await message.answer(MESSAGES_DICT['yes_or_no'][preferred_lang], reply_markup=ReplyKeyboardMarkup(
            keyboard=[
                [
                    KeyboardButton(text=MESSAGES_DICT['yes'][preferred_lang]),
                    KeyboardButton(text=MESSAGES_DICT['no'][preferred_lang]),
                ]
            ], resize_keyboard=True
        ))
        return
    
def generate_dummy_email(prefix: str, external_id: int) -> str:
    return f"{prefix}.{external_id}@dummy.com"

def extract_external_id(email: str) -> int:
    return int(email.split('@')[0].split('.')[1])

def validated_past_date(date_string, date_formats=['%d.%m.%Y', '%Y-%m-%d', '%m/%d/%Y']) -> datetime:
    """
    Validates a date string and checks if it represents a past date.

    Args:
        date_string (str): The date string to validate.
        date_formats (list): A list of date formats to try parsing.

    Returns:
        datetime: A datetime object representing the validated past date.
        Raises ValueError if the date is invalid or not in the past.
    """
    for fmt in date_formats:
        try:
            date_obj = datetime.strptime(date_string, fmt)
            if date_obj < datetime.now():
                return date_obj
            else:
                raise ValueError("Date must be in the past.")
        except ValueError as e:
            if "time data" in str(e):
                raise ValueError(f"Invalid date format. Please use one of these formats: {', '.join(date_formats)}")
            elif "Date must be in the past" in str(e):
                raise ValueError("Date must be in the past.")

    raise ValueError(f"Invalid date format or date not in the past. Please use one of these formats: {', '.join(date_formats)}")


class DailyCheckStates(StatesGroup):
    waiting_for_level = State()
    waiting_for_notes = State()

def get_level_keyboard(preferred_lang: str) -> ReplyKeyboardMarkup:

    keyboard = []
    for i in range(1, 6):
        keyboard.append(KeyboardButton(text=str(i)))
    
    return ReplyKeyboardMarkup(keyboard=[keyboard], resize_keyboard=True)
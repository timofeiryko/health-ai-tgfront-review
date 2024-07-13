import asyncio
import logging
import os, sys

from aiogram import Bot, Dispatcher, html, F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart, Command
from aiogram.types import (
    KeyboardButton,
    Message,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
)
from aiogram.fsm.context import FSMContext

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.redis import RedisJobStore
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.storage.base import StorageKey
from apscheduler_di import ContextSchedulerDecorator

from translated_messages import MESSAGES_DICT
from utils import RegistrationStates, DailyCheckStates, get_lang_keyboard, get_sex_keyboard, get_level_keyboard
from utils import check_extract_lang, eats_choice_handler, validated_past_date, generate_dummy_email
from to_api_utils import save_user_form, set_profile_fields, get_async_client, BACKEND_API_ENDPOINT, HEADERS

TOKEN = os.getenv('TG_BOT_TOKEN')
bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
storage = MemoryStorage()

JOBSTORES = {
    'default': RedisJobStore(jobs_key='jobs', run_times_key='run_times', host='localhost', port=6379)
}

UPDATE_INTERVAL = 15

scheduler = ContextSchedulerDecorator(AsyncIOScheduler(jobstores=JOBSTORES))
scheduler.ctx.add_instance(bot, Bot)

# All handlers should be attached to the Router (or Dispatcher)
dp = Dispatcher()
    
# <<<--->>>
# HANDLERS

@dp.message(CommandStart())
async def command_start_handler(message: Message, state: FSMContext) -> None:
    """
    This handler receives messages with `/start` command
    """
    
    await state.set_state(RegistrationStates.language)
    message_text = f"Hello, {html.bold(message.from_user.full_name)}! Please, chose a language:"
    await message.answer(message_text, reply_markup = get_lang_keyboard())

# TODO: ANOTHER COMMAND AND FDSM TO CHANGE LANGUAGE PROFILE SETTINGS, NOT JUST /start COMMAND
    
@dp.message(RegistrationStates.language)
async def process_lang(message: Message, state: FSMContext) -> None:
    """
    This handler receives user language preference, checks that it is supported and saves, if all is ok
    """

    preferred_lang = check_extract_lang(message=message)

    if preferred_lang:

        # save the user to the database
        user_data = {
            'full_name': message.from_user.full_name,
            'external_id': message.from_user.id,
            'preferred_lang': preferred_lang
        }

        async with get_async_client() as client:
            await save_user_form(registration_form=user_data, client=client)

        await state.update_data(preferred_lang=preferred_lang)
        # get the current state
        current_state = await state.get_state()
        if current_state == RegistrationStates.language:
            await state.set_state(RegistrationStates.profile_or_skip)
            message_text = MESSAGES_DICT['profile_or_skip'][preferred_lang]
            await message.answer(message_text, reply_markup=ReplyKeyboardMarkup(
                keyboard=[
                    [
                        KeyboardButton(text=MESSAGES_DICT['profile'][preferred_lang]),
                        KeyboardButton(text=MESSAGES_DICT['skip'][preferred_lang]),
                    ]
                ],
                resize_keyboard=True
            ))
        # elif current_state == RegistrationStates.change_language:
        #     await state.clear()
        #     message_text = MESSAGES_DICT['completed'][preferred_lang]
        #     await message.answer(message_text, reply_markup=ReplyKeyboardRemove())
        else:
            raise ValueError("Unexpected state")
    else:
        message_text = f"I am sorry, but this language is not supported. Please, choose from the available options using the keyboard:"
        await message.answer(message_text, reply_markup = get_lang_keyboard())

@dp.message(RegistrationStates.profile_or_skip)
async def process_profile_or_skip(message: Message, state: FSMContext) -> None:
    """
    This handler receives user choice to fill the profile or skip it
    """

    data = await state.get_data()
    preferred_lang = data['preferred_lang']

    if message.text == MESSAGES_DICT['profile'][preferred_lang]:
        await state.set_state(RegistrationStates.birth_date)
        message_text = MESSAGES_DICT['birth_date'][preferred_lang]
        await message.answer(message_text, reply_markup=ReplyKeyboardRemove())
    elif message.text == MESSAGES_DICT['skip'][preferred_lang]:
        await state.set_state(RegistrationStates.description)
        message_text = MESSAGES_DICT['description'][preferred_lang]
        await message.answer(message_text, reply_markup=ReplyKeyboardRemove())
    else:
        message_text = MESSAGES_DICT['yes_or_no'][preferred_lang]
        await message.answer(message_text, reply_markup=ReplyKeyboardMarkup(
            keyboard=[
                [
                    KeyboardButton(text=MESSAGES_DICT['profile'][preferred_lang]),
                    KeyboardButton(text=MESSAGES_DICT['skip'][preferred_lang]),
                ]
            ],
            resize_keyboard=True
        ))
    
@dp.message(RegistrationStates.birth_date)
async def process_birth_date(message: Message, state: FSMContext) -> None:
    """
    This handler receives user birth date
    """

    data = await state.get_data()
    preferred_lang = data['preferred_lang']

    try:
        dt = validated_past_date(message.text)
    except ValueError:
        await state.set_state(RegistrationStates.birth_date)
        message_text = MESSAGES_DICT['birth_date'][preferred_lang]
        await message.answer(message_text)
        return

    await state.update_data(birth_date=dt.strftime('%Y-%m-%d'))
    await state.set_state(RegistrationStates.sex)
    message_text = MESSAGES_DICT['sex'][preferred_lang]
    await message.answer(message_text, reply_markup=get_sex_keyboard(preferred_lang))

@dp.message(RegistrationStates.sex)
async def process_sex(message: Message, state: FSMContext) -> None:
    """This handler receives sex choice"""
    
    data = await state.get_data()
    preferred_lang = data['preferred_lang']
    
    if message.text == MESSAGES_DICT['male'][preferred_lang]:
        await state.update_data(sex='M')
        await state.set_state(RegistrationStates.mass)
        await message.answer(MESSAGES_DICT['mass'][preferred_lang], reply_markup=ReplyKeyboardRemove())
        
    elif message.text == MESSAGES_DICT['female'][preferred_lang]:
        await state.update_data(sex='F')
        await state.set_state(RegistrationStates.mass)
        await message.answer(MESSAGES_DICT['mass'][preferred_lang], reply_markup=ReplyKeyboardRemove())
        
    elif message.text == MESSAGES_DICT['other'][preferred_lang]:
        await state.update_data(sex='O')
        await state.set_state(RegistrationStates.mass)
        await message.answer(MESSAGES_DICT['mass'][preferred_lang], reply_markup=ReplyKeyboardRemove())
    
    else:
        await message.answer(MESSAGES_DICT['yes_or_no'][preferred_lang], reply_markup=get_sex_keyboard(preferred_lang))
        return


@dp.message(RegistrationStates.mass)
async def process_mass(message: Message, state: FSMContext) -> None:
    """
    This handler receives user mass
    """

    data = await state.get_data()
    preferred_lang = data['preferred_lang']
    await state.update_data(mass=message.text)
    await state.set_state(RegistrationStates.height)
    message_text = MESSAGES_DICT['height'][preferred_lang]
    await message.answer(message_text)

@dp.message(RegistrationStates.height)
async def process_height(message: Message, state: FSMContext) -> None:
    """
    This handler receives user height
    """

    data = await state.get_data()
    preferred_lang = data['preferred_lang']
    await state.update_data(height=message.text)
    await state.set_state(RegistrationStates.eats_meat)
    message_text = MESSAGES_DICT['eats_meat'][preferred_lang]
    await message.answer(message_text, reply_markup=ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text=MESSAGES_DICT['yes'][preferred_lang]),
                KeyboardButton(text=MESSAGES_DICT['no'][preferred_lang]),
            ]
        ],
        resize_keyboard=True
    ))

@dp.message(RegistrationStates.eats_meat)
async def process_eats_meat(message: Message, state: FSMContext) -> None:
    """
    This handler receives user choice if he/she eats meat
    """
    data = await state.get_data()
    preferred_lang = data['preferred_lang']
    next_message = MESSAGES_DICT['eats_fish'][preferred_lang]
    await eats_choice_handler(message, state, RegistrationStates.eats_fish, next_message)
    # save from eats attribute to the eats_meat of the state
    data = await state.get_data()
    await state.update_data(eats_meat=data['eats'])

@dp.message(RegistrationStates.eats_fish)
async def process_eats_fish(message: Message, state: FSMContext) -> None:
    """
    This handler receives user choice if he/she eats fish
    """
    data = await state.get_data()
    preferred_lang = data['preferred_lang']
    next_message = MESSAGES_DICT['eats_dairy'][preferred_lang]
    await eats_choice_handler(message, state, RegistrationStates.eats_dairy, next_message)
    data = await state.get_data()
    await state.update_data(eats_fish=data['eats'])


@dp.message(RegistrationStates.eats_dairy)
async def process_eats_dairy(message: Message, state: FSMContext) -> None:
    """
    This handler receives user choice if he/she eats dairy
    """
    data = await state.get_data()
    preferred_lang = data['preferred_lang']
    await eats_choice_handler(message, state, RegistrationStates.description, MESSAGES_DICT['description'][preferred_lang], last=True)
    data = await state.get_data()
    await state.update_data(eats_dairy=data['eats'])

@dp.message(RegistrationStates.description)
async def process_description(message: Message, state: FSMContext) -> None:
    """
    This handler receives user description
    """
    data = await state.get_data()
    preferred_lang = data['preferred_lang']
    await state.update_data(description=message.text)
    await state.set_state(RegistrationStates.completed)
    message_text = MESSAGES_DICT['saving_info'][preferred_lang]
    await message.answer(message_text)
    await all_saved(message, state)
            
@dp.message(RegistrationStates.completed)
async def all_saved(message: Message, state: FSMContext) -> None:
    """
    This handler confirms that all the settings are saved
    """
    
    data = await state.get_data()
    # TODO VERY BAD
    if 'birth_date' not in data or 'sex' not in data or 'mass' not in data or 'height' not in data or 'eats_meat' not in data or 'eats_fish' not in data or 'eats_dairy' not in data:
        # just save the profile with preferred_lang and exit
        profile_data = {
            'preferred_lang': data['preferred_lang'],
            'name': message.from_user.first_name,
            'description': data['description']
        }
    else:
        try:
            profile_data = {
                'name': message.from_user.first_name,
                'preferred_lang': data['preferred_lang'],
                'birth_date': data['birth_date'],
                'sex': data['sex'],
                'mass': int(data['mass']),
                'height': int(data['height']),
                'eats_meat': data['eats_meat'],
                'eats_fish': data['eats_fish'],
                'eats_dairy': data['eats_dairy'],
                'description': data['description']
            }
        except Exception as e:
            logging.error(f"Error while parsing the profile: {e}")
            await state.set_state(RegistrationStates.language)
            # REMOVE SHOWING ERROR MESSAGE IN PRODUCTION
            await message.answer(f'An error occurred while parsing the profile data. Probably, you have a typo in mass or height.\n\nPlease, try again. Choose a language:', reply_markup = get_lang_keyboard())
            return

    # TODO ability to skip height and mass (person may not know it)

    email = generate_dummy_email('tg', message.from_user.id)

    try:
        async with get_async_client() as client:
            await set_profile_fields(profile_fields=profile_data, user_email=email, client=client)
    except Exception as e:
        logging.error(f"Error while saving the profile: {e}")
        await state.set_state(RegistrationStates.language)
        # REMOVE SHOWING ERROR MESSAGE IN PRODUCTION
        await message.answer(f'An error occurred while saving the profile data. Probably, you have a typo in mass or height\n\nPlease, try again. Choose a language:', reply_markup = get_lang_keyboard())
        return

    preferred_lang = data['preferred_lang']
    await message.answer(MESSAGES_DICT['completed'][preferred_lang], reply_markup=ReplyKeyboardRemove())
    await initial_consultation(message, state)
    await state.set_state(RegistrationStates.consulting)

# TODO to utils.py
def get_consultation_markup(preferred_lang: str):
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text=MESSAGES_DICT['complete_consultation'][preferred_lang])
            ]
        ], resize_keyboard=True
    )

@dp.message(RegistrationStates.completed)
async def initial_consultation(message: Message, state: FSMContext) -> None:
    """
    This handler starts the initial consultation
    """
    
    try:

        user_id = message.from_user.id
        email = generate_dummy_email('tg', user_id)

        async with get_async_client() as client:
            response = await client.get(f'{BACKEND_API_ENDPOINT}/profiles/email/{email}', headers=HEADERS)
        preferred_lang = response.json()['preferred_lang']
        # send typing action
        await message.bot.send_chat_action(chat_id=message.chat.id, action='typing')
        async with get_async_client() as client:
            response = await client.get(f'{BACKEND_API_ENDPOINT}/users/email/{email}', headers=HEADERS)
            response.raise_for_status()
            
        user_email = response.json()['email']
        async with get_async_client() as client:

            response = await client.get(f'{BACKEND_API_ENDPOINT}/chat/{user_email}/start', headers=HEADERS)
            
        # update state with thread_id and preferred_lang
        await state.update_data(thread_id=response.json()['thread_id'])
        await state.update_data(preferred_lang=preferred_lang)
        

        await state.set_state(RegistrationStates.consulting)
        await message.answer(
            text=response.json()['text'],
            reply_markup=get_consultation_markup(preferred_lang),
            parse_mode=ParseMode.MARKDOWN
        )
    
    except Exception as e:
        logging.error(f"Error while starting the initial consultation: {e}")
        await message.answer("An error occurred while starting the initial consultation. Please, try again later. Take into account that images or voice messages are not supported yet. Try to wake me up with /start command!")

    
@dp.message(RegistrationStates.consulting)
async def consult(message: Message, state: FSMContext) -> None:
    """This handler consults the user and finishes the consultation, saving summary to the database through API"""
    
    try:
    
        data = await state.get_data()
        thread_id = data['thread_id']
        preferred_lang = data['preferred_lang']
        user_email = generate_dummy_email('tg', message.from_user.id)
        
        if message.text == MESSAGES_DICT['complete_consultation'][preferred_lang]:
            # typing action
            await message.bot.send_chat_action(chat_id=message.chat.id, action='typing')
            async with get_async_client() as client:
                response = await client.get(f'{BACKEND_API_ENDPOINT}/chat/{user_email}/complete/{thread_id}', headers=HEADERS)
                response.raise_for_status()
            message_text = response.json()['text']

            await state.set_state(RegistrationStates.initial_consultation_completed)
            await message.answer(message_text, reply_markup=ReplyKeyboardRemove(), parse_mode=ParseMode.MARKDOWN)

            # Send regular messages to this user
            scheduler.add_job(send_daily_check_message, 'interval', seconds=UPDATE_INTERVAL, kwargs={'telegram_id': message.from_user.id}, id=f'{message.from_user.id}_test', replace_existing=True)
            
        else:
            # continue the consultation
            # typing action
            await message.bot.send_chat_action(chat_id=message.chat.id, action='typing')
            async with get_async_client() as client:
                response = await client.get(f'{BACKEND_API_ENDPOINT}/chat/{user_email}/message/{thread_id}', headers=HEADERS, params={'text': message.text})
                response.raise_for_status()
            message_text = response.json()['text']
            await message.answer(
                text=message_text,
                reply_markup=get_consultation_markup(preferred_lang),
                parse_mode=ParseMode.MARKDOWN
            )
    
    except Exception as e:
        logging.error(f"Error while sending the message: {e}")
        await message.answer("An error occurred while sending the message. Please, try again later. Take into account that images or voice messages are not supported yet. Try to wake me up with /start command!")
    

@dp.message(F.text, Command('test'))
async def test(message: Message, state: FSMContext) -> None:
    """This handler is for testing purposes"""
    scheduler.add_job(send_daily_check_message, 'interval', seconds=UPDATE_INTERVAL, kwargs={'telegram_id': message.from_user.id}, id=f'{message.from_user.id}_test', replace_existing=True)
    await message.answer("Test job is scheduled")

async def send_daily_check_message(telegram_id: str, bot: Bot = None) -> None:
    """Sends a daily check message to the user"""

    email = generate_dummy_email('daily_check', telegram_id)
    print(f"Sending daily check message to {email}")
    # later we will generate message using API, but for now we will just send a dummy message
    message_text = "How are you feeling today? Please rate your mood from 1 to 10."

    # change state to waiting_for_level
    key = StorageKey(bot.id, telegram_id, telegram_id)
    user_context = FSMContext(dp.storage, key)
    await user_context.set_state(DailyCheckStates.waiting_for_level)
    state = await user_context.get_state()
    print(f"State: {state}")
    await bot.send_message(chat_id=telegram_id, text=message_text, reply_markup=get_level_keyboard('en'))

@dp.message(DailyCheckStates.waiting_for_level)
async def daily_check(message: Message, state: FSMContext) -> None:
    """
    This handler receives the daily check answers
    """

    print('PROCESSING LEVEL')

    # check that the message text is on of the numbers from 1 to 10, ask to use keyboard if not
    if message.text not in [str(i) for i in range(1, 11)]:
        correct_message_text = MESSAGES_DICT['yes_or_no']['en'] # TODO get the preferred_lang from the user data
        await message.answer(correct_message_text, reply_markup=get_level_keyboard('en'))
        return

    user_email = generate_dummy_email('tg', message.from_user.id)
    level = int(message.text)
    print(f"Level: {level} for user {user_email} ready to save")

    await state.set_state(DailyCheckStates.waiting_for_notes)
    await message.answer("Thank you for your answer! Your mood level is saved. Now add some notes")

@dp.message(DailyCheckStates.waiting_for_notes)
async def daily_check_notes(message: Message, state: FSMContext) -> None:
    """
    This handler receives the daily check notes
    """

    user_email = generate_dummy_email('tg', message.from_user.id)
    notes = message.text
    print(f"Notes: {notes} for user {user_email} ready to save")

    await state.set_state(RegistrationStates.initial_consultation_completed)
    await message.answer("Thank you for your notes! Your notes are saved. Have a nice day!")

@dp.message(F.text)
async def default_answer(message: Message, state: FSMContext) -> None:
    """
    This handler reacts to all other messages, it is similar to consult, but without completing the consultation
    """

    state = await state.get_state()
    print(f"ACTUAL STATE: {state}")

    # typing action
    # TODO: FIX THIS
    try:
        user_email = generate_dummy_email('tg', message.from_user.id)
        data = await state.get_data()
        thread_id = data['thread_id'] # TODO: FIX check if thread_id is in the data and don't use it if it's not (start a new thread)
        await message.bot.send_chat_action(chat_id=message.chat.id, action='typing')
        async with get_async_client() as client:
            response = await client.get(f'{BACKEND_API_ENDPOINT}/chat/{user_email}/message/{thread_id}', headers=HEADERS, params={'text': message.text})
            response.raise_for_status()
        message_text = response.json()['text']
        await message.answer(message_text, parse_mode=ParseMode.MARKDOWN)
    except Exception as e:
        logging.error(f"Error while sending the message: {e}")
        await message.answer("An error occurred while sending the message. Please, try again later. Take into account that images or voice messages are not supported yet. Try to wake me up with /start command!")




async def main() -> None:
    # Initialize Bot instance with default bot properties which will be passed to all API calls
    scheduler.start()
    # And the run events dispatching
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
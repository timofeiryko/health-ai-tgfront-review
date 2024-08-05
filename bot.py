import asyncio
import logging
import os, sys
import traceback

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
from utils import RegistrationStates, DailyCheckStates, get_lang_keyboard, get_sex_keyboard, get_level_keyboard, get_mass_options_keyboard, get_height_options_keyboard, get_consultation_markup
from utils import check_extract_lang, eats_choice_handler, validated_past_date, generate_dummy_email
from to_api_utils import save_user_form, set_profile_fields, get_async_client, BACKEND_API_ENDPOINT, HEADERS
from voice import voice_to_text, clean_audio_file

TOKEN = os.getenv('TG_BOT_TOKEN')
bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
storage = MemoryStorage()

JOBSTORES = {
    'default': RedisJobStore(jobs_key='jobs', run_times_key='run_times', host='localhost', port=6379)
}

UPDATE_INTERVAL = 60 * 5

scheduler = ContextSchedulerDecorator(AsyncIOScheduler(jobstores=JOBSTORES))
scheduler.ctx.add_instance(bot, Bot)

# All handlers should be attached to the Router (or Dispatcher)
dp = Dispatcher()

# Bot can understand text and voice messages
SUPPORTED_CONTENT_TYPES = ['text', 'voice']
# mkdir files
if not os.path.exists('files'):
    os.makedirs('files')
    
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
            'preferred_lang': preferred_lang,
        }

        async with get_async_client() as client:
            await save_user_form(registration_form=user_data, client=client)

        await state.update_data(preferred_lang=preferred_lang)
        # get the current state
        current_state = await state.get_state()
        if current_state == RegistrationStates.language:
            await state.set_state(RegistrationStates.sex)
            message_text = f"{MESSAGES_DICT['profile_or_skip'][preferred_lang]}\n\n{MESSAGES_DICT['sex'][preferred_lang]}"
            await message.answer(message_text, reply_markup=get_sex_keyboard(preferred_lang))
        # elif current_state == RegistrationStates.change_language:
        #     await state.clear()
        #     message_text = MESSAGES_DICT['completed'][preferred_lang]
        #     await message.answer(message_text, reply_markup=ReplyKeyboardRemove())
        else:
            raise ValueError("Unexpected state")
    else:
        message_text = f"I am sorry, but this language is not supported. Please, choose from the available options using the keyboard:"
        await message.answer(message_text, reply_markup = get_lang_keyboard())

# @dp.message(RegistrationStates.profile_or_skip)
# async def process_profile_or_skip(message: Message, state: FSMContext) -> None:
#     """
#     This handler receives user choice to fill the profile or skip it
#     """

#     data = await state.get_data()
#     preferred_lang = data['preferred_lang']

#     if message.text == MESSAGES_DICT['profile'][preferred_lang]:
#         await state.set_state(RegistrationStates.birth_date)
#         message_text = MESSAGES_DICT['birth_date'][preferred_lang]
#         await message.answer(message_text, reply_markup=ReplyKeyboardRemove())
#     elif message.text == MESSAGES_DICT['skip'][preferred_lang]:
#         await state.set_state(RegistrationStates.description)
#         message_text = MESSAGES_DICT['description'][preferred_lang]
#         await message.answer(message_text, reply_markup=ReplyKeyboardRemove())
#     else:
#         message_text = MESSAGES_DICT['yes_or_no'][preferred_lang]
#         await message.answer(message_text, reply_markup=ReplyKeyboardMarkup(
#             keyboard=[
#                 [
#                     KeyboardButton(text=MESSAGES_DICT['profile'][preferred_lang]),
#                     KeyboardButton(text=MESSAGES_DICT['skip'][preferred_lang]),
#                 ]
#             ],
#             resize_keyboard=True
#         ))
    
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
        await state.set_state(RegistrationStates.height)
        await message.answer(MESSAGES_DICT['height'][preferred_lang], reply_markup=get_height_options_keyboard(preferred_lang))
        
    elif message.text == MESSAGES_DICT['female'][preferred_lang]:
        await state.update_data(sex='F')
        await state.set_state(RegistrationStates.height)
        await message.answer(MESSAGES_DICT['height'][preferred_lang], reply_markup=get_height_options_keyboard(preferred_lang))
        
    elif message.text == MESSAGES_DICT['other'][preferred_lang]:
        await state.update_data(sex='O')
        await state.set_state(RegistrationStates.height)
        await message.answer(MESSAGES_DICT['height'][preferred_lang], reply_markup=get_height_options_keyboard(preferred_lang))
    
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
    height = data['height']
    
    if message.text == MESSAGES_DICT['mass_option_low'][preferred_lang]:
        bmi = 19
        mass = round(bmi * (height / 100) ** 2)
        await state.update_data(mass=mass)
    elif message.text == MESSAGES_DICT['mass_option_average'][preferred_lang]:
        bmi = 22
        mass = round(bmi * (height / 100) ** 2)
        await state.update_data(mass=mass)
    elif message.text == MESSAGES_DICT['mass_option_high'][preferred_lang]:
        bmi = 26
        mass = round(bmi * (height / 100) ** 2)
        await state.update_data(mass=mass)
    elif message.text in [str(i) for i in range(2, 1000)]:
        await state.update_data(mass=message.text)
    else:
        message_text = MESSAGES_DICT['mass'][preferred_lang]
        await message.answer(message_text, reply_markup=get_mass_options_keyboard(preferred_lang))
        return
    
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

@dp.message(RegistrationStates.height)
async def process_height(message: Message, state: FSMContext) -> None:
    """
    This handler receives user height
    """

    data = await state.get_data()
    preferred_lang = data['preferred_lang']
    sex = data['sex']
    
    if message.text == MESSAGES_DICT['height_option_low'][preferred_lang] and (sex == 'M' or sex == 'O'):
        await state.update_data(height=165)
    elif message.text == MESSAGES_DICT['height_option_low'][preferred_lang] and sex == 'F':
        await state.update_data(height=155)
    elif message.text == MESSAGES_DICT['height_option_average'][preferred_lang] and (sex == 'M' or sex == 'O'):
        await state.update_data(height=175)
    elif message.text == MESSAGES_DICT['height_option_average'][preferred_lang] and sex == 'F':
        await state.update_data(height=165)
    elif message.text == MESSAGES_DICT['height_option_high'][preferred_lang] and (sex == 'M' or sex == 'O'):
        await state.update_data(height=185)
    elif message.text == MESSAGES_DICT['height_option_high'][preferred_lang] and sex == 'F':
        await state.update_data(height=175)
    elif message.text in [str(i) for i in range(50, 300)]:
        await state.update_data(height=message.text)
    else:
        message_text = MESSAGES_DICT['height'][preferred_lang]
        await message.answer(message_text, reply_markup=get_height_options_keyboard(preferred_lang))
        return
    
    await state.set_state(RegistrationStates.mass)
    message_text = MESSAGES_DICT['mass'][preferred_lang]
    await message.answer(message_text, reply_markup=get_mass_options_keyboard(preferred_lang))
    

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
    await eats_choice_handler(message, state, RegistrationStates.description, MESSAGES_DICT['saving_info'][preferred_lang], last=True)
    data = await state.get_data()
    await state.update_data(eats_dairy=data['eats'])
    
    await state.set_state(RegistrationStates.description)
    message_text = MESSAGES_DICT['description'][preferred_lang]
    await message.answer(message_text, reply_markup=ReplyKeyboardRemove())

@dp.message(RegistrationStates.description)
async def process_description(message: Message, state: FSMContext) -> None:
    """
    This handler receives user description
    """
    
    # Check that message is in supported content types
    if message.content_type not in SUPPORTED_CONTENT_TYPES:
        await message.answer("Sorry, but I can't process this type of message. Please, use text or voice messages.")
        return
    
    data = await state.get_data()
    preferred_lang = data['preferred_lang']
    
    if message.content_type == 'text':
        await state.update_data(description=message.text)
        
    elif message.content_type == 'voice':
        
        file_id = message.voice.file_id  
        file = await bot.get_file(file_id)  
        file_path = file.file_path  
        file_name = f"files/audio{file_id}.mp3"
        await bot.download_file(file_path, file_name)
        
        transcription = await voice_to_text(file_name, preferred_lang)
        await clean_audio_file(f"files/audio{file_id}.mp3")
        await state.update_data(description=transcription)
        
    await state.set_state(RegistrationStates.completed)
    message_text = MESSAGES_DICT['saving_info'][preferred_lang]
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
            logging.error(f"Error while parsing the profile: {e}. More info:\n {traceback.format_exc()}")
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
        logging.error(f"Error while saving the profile: {e}. More info:\n {traceback.format_exc()}")
        await state.set_state(RegistrationStates.language)
        # REMOVE SHOWING ERROR MESSAGE IN PRODUCTION
        await message.answer(f'An error occurred while saving the profile data. Probably, you have a typo in mass or height\n\nPlease, try again. Choose a language:', reply_markup = get_lang_keyboard())
        return

    preferred_lang = data['preferred_lang']
    await message.answer(MESSAGES_DICT['completed'][preferred_lang], reply_markup=ReplyKeyboardRemove())
    await initial_consultation(message, state)
    await state.set_state(RegistrationStates.consulting)


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
            
            response = await client.get(f'{BACKEND_API_ENDPOINT}/chat/{user_email}/start', headers=HEADERS)
            response.raise_for_status()
            thread_id = response.json()['thread_id']
            raw_text = response.json()['text']
            
            response = await client.get(f'{BACKEND_API_ENDPOINT}/chat/{user_email}/split', headers=HEADERS, params={'advice': raw_text})
            response.raise_for_status()
            message_text = response.json()['text']            

        await state.update_data(thread_id=thread_id)
        await state.update_data(preferred_lang=preferred_lang)
        

        await state.set_state(RegistrationStates.consulting)
        await message.answer(
            text=message_text,
            reply_markup=ReplyKeyboardRemove(),
            parse_mode=ParseMode.MARKDOWN
        )
        
        # Send regular messages to this user
        scheduler.add_job(send_daily_initial_piece, 'interval', seconds=UPDATE_INTERVAL, kwargs={'telegram_id': message.from_user.id}, id=f'{message.from_user.id}_initial_consultation', replace_existing=True)
    
    except Exception as e:
        logging.error(f"Error while starting the initial consultation: {e}. More info:\n {traceback.format_exc()}")
        await message.answer("An error occurred while starting the initial consultation. Please, try again later. Take into account that images or voice messages are not supported yet. Try to wake me up with /start command!")

    
@dp.message(RegistrationStates.consulting)
async def consult(message: Message, state: FSMContext) -> None:
    """This handler consults the user and finishes the consultation, saving summary to the database through API"""
    
    # Check that message is in supported content types
    if message.content_type not in SUPPORTED_CONTENT_TYPES:
        await message.answer("Sorry, but I can't process this type of message. Please, use text or voice messages.")
        return
    
    data = await state.get_data()
    preferred_lang = data['preferred_lang']
    
    if message.content_type == 'text':
        message_text = message.text
        
    elif message.content_type == 'voice':
        
        file_id = message.voice.file_id  
        file = await bot.get_file(file_id)  
        file_path = file.file_path  
        file_name = f"files/audio{file_id}.mp3"
        await bot.download_file(file_path, file_name)
        
        transcription = await voice_to_text(file_name, preferred_lang)
        await clean_audio_file(f"files/audio{file_id}.mp3")
        message_text = transcription
    
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
                response = await client.get(f'{BACKEND_API_ENDPOINT}/chat/{user_email}/message/{thread_id}', headers=HEADERS, params={'text': message_text})
                response.raise_for_status()
            message_text = response.json()['text']
            await message.answer(
                text=message_text,
                reply_markup=ReplyKeyboardRemove(),
                parse_mode=ParseMode.MARKDOWN
            )
    
    except Exception as e:
        logging.error(f"Error while sending the message: {e}. More info:\n {traceback.format_exc()}")
        traceback.print_exc()
        await message.answer("An error occurred while sending the message. Please, try again later. Take into account that images or voice messages are not supported yet. Try to wake me up with /start command!")
    

@dp.message(F.text, Command('test'))
async def test(message: Message, state: FSMContext) -> None:
    """This handler is for testing purposes"""
    scheduler.add_job(send_daily_check_message, 'interval', seconds=UPDATE_INTERVAL, kwargs={'telegram_id': message.from_user.id}, id=f'{message.from_user.id}_test', replace_existing=True)
    await message.answer("Test job is scheduled")

async def send_daily_check_message(telegram_id: str, bot: Bot = None) -> None:
    """Sends a daily check message to the user"""

    user_email = generate_dummy_email('tg', telegram_id)
    async with get_async_client() as client:
        response = await client.get(f'{BACKEND_API_ENDPOINT}/chat/{user_email}/greet', headers=HEADERS)
        response.raise_for_status()
    message_text = response.json()

    # change state to waiting_for_level
    key = StorageKey(bot.id, telegram_id, telegram_id)
    user_context = FSMContext(dp.storage, key)
    await user_context.set_state(DailyCheckStates.waiting_for_notes)
    await user_context.update_data(greeting=message_text)
    await bot.send_message(chat_id=telegram_id, text=message_text)
    
async def send_daily_initial_piece(telegram_id: str, bot: Bot = None) -> None:
    """Sends a daily piece of advice on the initial stage"""
    
    user_email = generate_dummy_email('tg', telegram_id)
    async with get_async_client() as client:
        response = await client.get(f'{BACKEND_API_ENDPOINT}/initial_advice_piece_count/{user_email}', headers=HEADERS)
        response.raise_for_status()
        number_of_pieces = int(response.json())
        if number_of_pieces == 0:
            
            # complete the initial consultation
            response = await client.get(f'{BACKEND_API_ENDPOINT}/chat/{user_email}/complete', headers=HEADERS)
            response.raise_for_status()
            
            # set the state to initial_consultation_completed
            key = StorageKey(bot.id, telegram_id, telegram_id)
            user_context = FSMContext(dp.storage, key)
            await user_context.set_state(RegistrationStates.initial_consultation_completed)
            
            # remove the job
            scheduler.remove_job(f'{telegram_id}_initial_consultation')
        else:
            response = await client.get(f'{BACKEND_API_ENDPOINT}/initial_advice_piece/{user_email}', headers=HEADERS)
            response.raise_for_status()
        
    message_text = response.json()['text']
    
    await bot.send_message(chat_id=telegram_id, text=message_text)


@dp.message(DailyCheckStates.waiting_for_level)
async def daily_check(message: Message, state: FSMContext) -> None:
    """
    This handler receives the daily check answers
    """
    
    # get preferred_lang from data
    data = await state.get_data()
    preferred_lang = data['preferred_lang']
    
    if message.text not in [str(i) for i in range(1, 6)]:
        correct_message_text = MESSAGES_DICT['yes_or_no'][preferred_lang]
        await message.answer(correct_message_text, reply_markup=get_level_keyboard(preferred_lang))
        return

    user_email = generate_dummy_email('tg', message.from_user.id)
    level = int(message.text)
    data = await state.get_data()
    notes = data['notes']
    greeting = data['greeting']
    
    
    async with get_async_client() as client:
        response = await client.get(f'{BACKEND_API_ENDPOINT}/chat/{user_email}/daily_advice', headers=HEADERS, params={
            'greeting': greeting,
            'user_notes': notes,
            'overall_feeling_level': level
        })
        response.raise_for_status()
        
    thread_id = response.json()['thread_id']
    message_text = response.json()['text']
    
    # update state with thread_id
    await state.update_data(thread_id=thread_id)
    
    await state.set_state(RegistrationStates.initial_consultation_completed)
    await message.answer(message_text, reply_markup=ReplyKeyboardRemove())

@dp.message(DailyCheckStates.waiting_for_notes)
async def daily_check_notes(message: Message, state: FSMContext) -> None:
    """
    This handler receives the daily check notes
    """

    user_email = generate_dummy_email('tg', message.from_user.id)
    notes = message.text
    await state.update_data(notes=notes)
    
    async with get_async_client() as client:
        response = await client.get(f'{BACKEND_API_ENDPOINT}/profiles/email/{user_email}', headers=HEADERS)
    preferred_lang = response.json()['preferred_lang']
    
    # update state with preferred_lang and greeting
    await state.update_data(preferred_lang=preferred_lang)

    await state.set_state(DailyCheckStates.waiting_for_level)
    await message.answer(MESSAGES_DICT['ask_lavel'][preferred_lang], reply_markup=get_level_keyboard(preferred_lang))

@dp.message(F.text)
async def default_answer(message: Message, state: FSMContext) -> None:
    """
    This handler reacts to all other messages, it is similar to consult, but without completing the consultation
    """

    if message.content_type not in SUPPORTED_CONTENT_TYPES:
        await message.answer("Sorry, but I can't process this type of message. Please, use text or voice messages.")
        return
    
    data = await state.get_data()
    preferred_lang = data['preferred_lang']
    
    if message.content_type == 'text':
        message_text = message.text
        
    elif message.content_type == 'voice':
        
        # TODO DRY
        
        file_id = message.voice.file_id  
        file = await bot.get_file(file_id)  
        file_path = file.file_path  
        file_name = f"files/audio{file_id}.mp3"
        await bot.download_file(file_path, file_name)
        
        transcription = await voice_to_text(file_name, preferred_lang)
        await clean_audio_file(f"files/audio{file_id}.mp3")
        message_text = transcription

    data = await state.get_data()
    user_email = generate_dummy_email('tg', message.from_user.id)
    
    # try to extract thread_id from data
    try:
        thread_id = data['thread_id']
    except KeyError:
        # for now just send error message
        # TODO: FIX check if thread_id is in the data and don't use it if it's not (start a new thread)
        await message.answer("An error occurred while sending the message. Please, try again later. Take into account that images or voice messages are not supported yet. Try to wake me up with /start command!")
    
    await message.bot.send_chat_action(chat_id=message.chat.id, action='typing')
    try:
        async with get_async_client() as client:
            response = await client.get(f'{BACKEND_API_ENDPOINT}/chat/{user_email}/message/{thread_id}', headers=HEADERS, params={'text': message_text})
            response.raise_for_status()
    except Exception as e:
        logging.error(f"Error while sending the message: {e}. More info:\n {traceback.format_exc()}")
        await message.answer("An error occurred while sending the message. Please, try again later. Take into account that images or voice messages are not supported yet. Try to wake me up with /start command!")
        return
    
    await message.answer(response.json()['text'], parse_mode=ParseMode.MARKDOWN)


async def main() -> None:
    # Initialize Bot instance with default bot properties which will be passed to all API calls
    scheduler.start()
    # And the run events dispatching
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
"""Functions to interact with the API service. These functions are actually not gelegram specific."""

from typing import Optional

from dotenv import load_dotenv
import os
import httpx
from retry import retry
from contextlib import asynccontextmanager

from utils import generate_dummy_email

load_dotenv()

HEADERS = {
    'X-API-KEY': os.getenv('BACKEND_API_KEY'),
}
BACKEND_API_ENDPOINT = os.getenv('BACKEND_API_ENDPOINT')

RETRY = httpx.AsyncHTTPTransport(retries=2)

def get_random_string(length: int) -> str:
    """Generates a random string of the given length"""
    return os.urandom(length).hex()

@asynccontextmanager
async def get_async_client():
    async with httpx.AsyncClient(transport=RETRY, timeout=20.0) as client:
        yield client

@retry(tries=2)
async def save_user_form(registration_form: dict, client: httpx.AsyncClient):
    """Creates a user through the API or updates the existing one"""

    # if there is no email, generate dummy email
    if not registration_form.get('email'):
        registration_form['email'] = generate_dummy_email('tg', registration_form['external_id'])

    # skip if user exists
    response = await client.get(f'{BACKEND_API_ENDPOINT}/users/email/{registration_form["email"]}', headers=HEADERS)
    if response.status_code == 200:
        return
    else:

        if not registration_form.get('password'):
            registration_form['password'] = f'generated_pass_{get_random_string(10)}'

        # extract only user fields from the registration form
        user_fields = ['email', 'password', 'full_name', 'is_staff', 'is_superuser']
        user_data = {key: registration_form.get(key) for key in user_fields if registration_form.get(key) is not None}

        # send the user data to the API
        response = await client.post(f'{BACKEND_API_ENDPOINT}/users', json=user_data, headers=HEADERS)
        response.raise_for_status()

        # TODO DON'T LOG PASSWORDS!!!

@retry(tries=2)
async def set_profile_fields(profile_fields: dict, user_id: Optional[dict]=None, user_email: Optional[str]=None, client: httpx.AsyncClient=None):
    """Saves the user profile fields to the API"""

    response = None
    if user_id is None and user_email is not None:
        response = await client.get(f'{BACKEND_API_ENDPOINT}/users/email/{user_email}', headers=HEADERS)
        response.raise_for_status()
        user_id = response.json()['id']

    # extract only profile fields from the registration form
    profile_fields_keys = ['name', 'preferred_lang', 'birth_date', 'sex', 'mass', 'height', 'eats_meat', 'eats_fish', 'eats_dairy', 'description', 'initial_summary']
    profile_fields = {key: profile_fields.get(key) for key in profile_fields_keys if profile_fields.get(key) is not None}

    # create profile if it doesn't exist
    response = await client.get(f'{BACKEND_API_ENDPOINT}/users/{user_id}/profile', headers=HEADERS)
    if response.status_code == 404:
        inner_response = await client.post(f'{BACKEND_API_ENDPOINT}/users/{user_id}/profile', json=profile_fields, headers=HEADERS)
        inner_response.raise_for_status()
    elif response.status_code == 200:
        inner_response = await client.patch(f'{BACKEND_API_ENDPOINT}/users/{user_id}/profile', json=profile_fields, headers=HEADERS)
        inner_response.raise_for_status()
    else:
        response.raise_for_status()
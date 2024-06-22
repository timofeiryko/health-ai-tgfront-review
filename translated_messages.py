from dataclasses import dataclass

@dataclass
class TranslatedMessage:
    en: str
    ru: str

    def __getitem__(self, key):
        return self.__dict__[key]

# This is just for accessing dict keys like an attribute
class AttrDict(dict):
    def __init__(self, *args, **kwargs):
        super(AttrDict, self).__init__(*args, **kwargs)
        self.__dict__ = self
    
MESSAGES_DICT: AttrDict[str, TranslatedMessage] = AttrDict({
    'completed': TranslatedMessage(
        en='Hooray, everything is saved! In case you want to change your profile, just send /start. I will be glad to help, feel free to ask any questions ☺️',
        ru='Ура, всё сохранено! Если захотите изменить профиль, просто отправьте /start. Буду рад помочь, не стесняйтесь задавать любые вопросы ☺️'
    ),
    'saving_info': TranslatedMessage(
        en='Saving your info...',
        ru='Сохраняю вашу информацию...'
    ),
    'profile_or_skip': TranslatedMessage(
        en='In order for my recommendations to be more accurate and personalized, we need to get to know each other a little better. Do you want to fill out a profile in 1 minute?',
        ru='Чтобы я мои рекомендации были точнее и более персонализированными, нам нужно познакомиться немного поближе. Хотите заполнить профиль за 1 минуту?'
    ),
    'profile': TranslatedMessage(
        en='Fill out the profile',
        ru='Заполнить профиль'
    ),
    'skip': TranslatedMessage(
        en='Skip',
        ru='Пропустить'
    ),
    'birth_date': TranslatedMessage(
        en='🗓 Please, enter your birth date in the format DD.MM.YYYY (YYYY-MM-DD, MM/DD/YYYY also work)',
        ru='🗓 Пожалуйста, введите вашу дату рождения в формате ДД.ММ.ГГГГ (ГГГГ-ММ-ДД, ММ/ДД/ГГГГ тоже подойдут)'
    ),
    'sex': TranslatedMessage(
        en='Now choose your biological sex 🙏',
        ru='Теперь выберите пол 🙏'
    ),
    'male': TranslatedMessage(
        en='Male 🕺',
        ru='Мужской 🕺'
    ),
    'female': TranslatedMessage(
        en='Female 🏃‍♀️',
        ru='Женский 🏃‍♀️'
    ),
    'other': TranslatedMessage(
        en='Other',
        ru='Другое 🐈'
    ),
    'mass': TranslatedMessage(
        en='Please, enter your mass in kg',
        ru='Пожалуйста, введите ваш вес в кг'
    ),
    'height': TranslatedMessage(
        en='🦒 Please, enter your height in cm',
        ru='🦒 Пожалуйста, введите ваш рост в см'
    ),
    'eats_meat': TranslatedMessage(
        en='🥩 Do you eat meat?',
        ru='🥩 Вы едите мясо?'
    ),
    'eats_fish': TranslatedMessage(
        en='🐟 Do you eat fish?',
        ru='🐟 Вы едите рыбу?'
    ),
    'eats_dairy': TranslatedMessage(
        en='🥛 Do you eat dairy products?',
        ru='🥛 Вы употребляете молочные продукты?'
    ),
    'eats_eggs': TranslatedMessage(
        en='🍳 Do you eat eggs?',
        ru='🍳 Вы едите яйца?'
    ),
    'yes': TranslatedMessage(
        en='👍 Yes',
        ru='👍 Да'
    ),
    'no': TranslatedMessage(
        en='🙅 No',
        ru='🙅 Нет'
    ),
    'yes_or_no': TranslatedMessage(
        en='Please, use the buttons below to answer',
        ru='Пожалуйста, воспользуйтесь кнопками ниже, чтобы ответить'
    ),
    'description': TranslatedMessage(
        en='📝 Please, briefly tell me about your goals regarding nutrition and fitness, add important details like your allrgies, food preferences, etc',
        ru='📝 Пожалуйста, кратко расскажите мне о ваших целях в области питания и фитнеса, добавьте важные детали, такие как ваша аллергия, предпочтения в еде и т.д.'
    ),
    'email': TranslatedMessage(
        en='📧 Please enter your email address. No spam or mailings!',
        ru='📧 Пожалуйста, введите ваш email. Никакого спама или рассылок!'
    ),
    'complete_consultation': TranslatedMessage(
        en='✅ Complete consultation',
        ru='✅ Завершить консультацию'
    )
})



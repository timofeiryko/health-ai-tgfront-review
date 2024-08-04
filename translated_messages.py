from dataclasses import dataclass

@dataclass
class TranslatedMessage:
    en: str
    ru: str
    es: str

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
        ru='Ура, всё сохранено! Если захотите изменить профиль, просто отправьте /start. Буду рад помочь, не стесняйтесь задавать любые вопросы ☺️',
        es='¡Hurra, todo está guardado! En caso de que desee cambiar su perfil, simplemente envíe /start. Estaré encantado de ayudar, no dude en hacer cualquier pregunta ☺️'
    ),
    'saving_info': TranslatedMessage(
        en='Saving your info...',
        ru='Сохраняю вашу информацию...',
        es='Guardando tu información...'
    ),
    'profile_or_skip': TranslatedMessage(
        en='In order for my recommendations to be more accurate and personalized, we need to get to know each other a little better ☺️',
        ru='Чтобы я мои рекомендации были более точными и персонализированными, нам нужно познакомиться немного поближе ☺️',
        es='Para que mis recomendaciones sean más precisas y personalizadas, necesitamos conocernos un poco mejor ☺️'
    ),
    'profile': TranslatedMessage(
        en='Fill out the profile',
        ru='Заполнить профиль',
        es='Completar el perfil'
    ),
    'skip': TranslatedMessage(
        en='Skip',
        ru='Пропустить',
        es='Saltar'
    ),
    'birth_date': TranslatedMessage(
        en='🗓 Please, enter your birth date in the format DD.MM.YYYY (YYYY-MM-DD, MM/DD/YYYY also work)',
        ru='🗓 Пожалуйста, введите вашу дату рождения в формате ДД.ММ.ГГГГ (ГГГГ-ММ-ДД, ММ/ДД/ГГГГ тоже подойдут)',
        es='🗓 Por favor, ingrese su fecha de nacimiento en el formato DD.MM.AAAA (AAAA-MM-DD, MM/DD/AAAA también funcionan)'
    ),
    'sex': TranslatedMessage(
        en='Now choose your biological sex 🙏',
        ru='Теперь выберите пол 🙏',
        es='Ahora elige tu sexo biológico 🙏'
    ),
    'male': TranslatedMessage(
        en='Male 🕺',
        ru='Мужской 🕺',
        es='Masculino 🕺'
    ),
    'female': TranslatedMessage(
        en='Female 🏃‍♀️',
        ru='Женский 🏃‍♀️',
        es='Femenino 🏃‍♀️'
    ),
    'other': TranslatedMessage(
        en='Other',
        ru='Другое 🐈',
        es='Otro 🐈'
    ),
    'mass': TranslatedMessage(
        en='Please, enter your mass in kg',
        ru='Пожалуйста, введите ваш вес в кг',
        es='Por favor, ingrese su masa en kg'
    ),
    'height': TranslatedMessage(
        en='🦒 Please, enter your height in cm',
        ru='🦒 Пожалуйста, введите ваш рост в см',
        es='🦒 Por favor, ingrese su altura en cm'
    ),
    'eats_meat': TranslatedMessage(
        en='🥩 Do you eat meat?',
        ru='🥩 Вы едите мясо?',
        es='🥩 ¿Comes carne?'
    ),
    'eats_fish': TranslatedMessage(
        en='🐟 Do you eat fish?',
        ru='🐟 Вы едите рыбу?',
        es='🐟 ¿Comes pescado?'
    ),
    'eats_dairy': TranslatedMessage(
        en='🥛 Do you eat dairy products?',
        ru='🥛 Вы употребляете молочные продукты?',
        es='🥛 ¿Comes productos lácteos?'
    ),
    'eats_eggs': TranslatedMessage(
        en='🍳 Do you eat eggs?',
        ru='🍳 Вы едите яйца?',
        es='🍳 ¿Comes huevos?'
    ),
    'yes': TranslatedMessage(
        en='👍 Yes',
        ru='👍 Да',
        es='👍 Sí'
    ),
    'no': TranslatedMessage(
        en='🙅 No',
        ru='🙅 Нет',
        es='🙅 No'

    ),
    'yes_or_no': TranslatedMessage(
        en='Please, use the buttons below to answer',
        ru='Пожалуйста, воспользуйтесь кнопками ниже, чтобы ответить',
        es='Por favor, use los botones de abajo para responder'
    ),
    'description': TranslatedMessage(
        en='📝 Please, briefly tell me about your goals regarding nutrition and fitness, add important details like your allrgies, food preferences, etc\n\n🗣 You can also use voice message!',
        ru='📝 Пожалуйста, кратко расскажите мне о ваших целях в области питания и фитнеса, добавьте важные детали, такие как ваша аллергия, предпочтения в еде и т.д.\n\n🗣 Вы также можете использовать голосовое сообщение!',
        es='📝 Por favor, cuéntame brevemente sobre tus objetivos en nutrición y fitness, agrega detalles importantes como tus alergias, preferencias alimentarias, etc.\n\n🗣 ¡También puedes usar mensajes de voz!'
    ),
    'email': TranslatedMessage(
        en='📧 Please enter your email address. No spam or mailings!',
        ru='📧 Пожалуйста, введите ваш email. Никакого спама или рассылок!',
        es='📧 Por favor, ingrese su dirección de correo electrónico. ¡Sin spam ni correos electrónicos!'
    ),
    'complete_consultation': TranslatedMessage(
        en='✅ Complete consultation',
        ru='✅ Завершить консультацию',
        es='✅ Consulta completa'
    ),
    'ask_lavel': TranslatedMessage(
        en='📈 What is your oveall feeling level for this day?',
        ru='📈 Каков ваш общий уровень самочувствия на этот день?',
        es='📈 ¿Cuál es su nivel de sensación general para este día?'
    ),
    'mass_option_low': TranslatedMessage(
        en="I don't know, but I'm thin",
        ru='Не знаю, но я худой',
        es='No lo sé, pero soy delgado'
    ),
    'mass_option_average': TranslatedMessage(
        en="I don't know, but I'm average",
        ru='Не знаю, но я средний',
        es='No lo sé, pero soy promedio'
    ),
    'mass_option_high': TranslatedMessage(
        en="I don't know, but I'm overweight",
        ru='Не знаю, но я полный',
        es='No lo sé, pero tengo sobrepeso'
    ),
    'height_option_low': TranslatedMessage(
        en="I don't know, but I'm short",
        ru='Не знаю, но я ниже среднего',
        es='No lo sé, pero soy bajo'
    ),
    'height_option_average': TranslatedMessage(
        en="I don't know, but I'm average",
        ru='Не знаю, но я среднего роста',
        es='No lo sé, pero soy promedio'
    ),
    'height_option_high': TranslatedMessage(
        en="I don't know, but I'm tall",
        ru='Не знаю, но я высокий',
        es='No lo sé, pero soy alto'
    ),
})



from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ParseMode
from telegram.ext import ConversationHandler

from data.utils import delete_last_message, get_config


@delete_last_message
def start(update, context):
    cfg = get_config()
    buttons = [
         [InlineKeyboardButton('Нужна помощь?', callback_data='help')],
         [InlineKeyboardButton('Перейти на сайт', url=cfg.get('URL клиники', 'https://belberry.net/'))],
         [InlineKeyboardButton('Позже', callback_data='later')]]
    phone = cfg.get('Номер телефона', 'Не указан')
    if len(phone.split(';')) > 1:
        phone = phone.split(';')[0]
    text = (f'Привет, %s! Я ассистент клиники <b>{cfg.get("Название клиники", "*")}</b>.\n'
            f'Я помогу узнать про нашу клинику подробнее.\n'
            f'Могу быстро записать на приём к доктору.\n'
            f'А также буду напоминать о приёме, актуальных акциях и индивидуальных предложениях 😊\n\n'
            f'Также со мной можно связаться по телефону: {phone}')
    if update.message:
        context.user_data['id'] = update.message.from_user.id
        context.user_data['first_name'] = update.message.from_user.first_name
    if str(context.user_data['id']) in cfg.get('admins', []):
        buttons.extend([[InlineKeyboardButton('Изменить данные (admin)', callback_data='data')],
                        [InlineKeyboardButton('Сбросить настройки (admin)', callback_data='ask')],
                        [InlineKeyboardButton('Добавить сущность (admin)', callback_data='add_menu')]])
    if cfg.get("Фото клиники"):
        return (context.bot.send_photo(context.user_data['id'], cfg["Фото клиники"],
                                       text % context.user_data['first_name'],
                                       reply_markup=InlineKeyboardMarkup(buttons), parse_mode=ParseMode.HTML),
                'menu')
    return (context.bot.send_message(context.user_data['id'], text % context.user_data['first_name'],
                                     reply_markup=InlineKeyboardMarkup(buttons), parse_mode=ParseMode.HTML),
            'menu')


@delete_last_message
def ask_for_help_menu(_, context):
    markup = InlineKeyboardMarkup(
        [[InlineKeyboardButton('Да 🤗', callback_data='yes')],
         [InlineKeyboardButton('Нет 😊', callback_data='no')],
         [InlineKeyboardButton('Вернуться назад', callback_data='back')]])
    return context.bot.send_message(context.user_data['id'], 'Нужна ли Вам помощь?',
                                    reply_markup=markup), 'ask_for_help'


@delete_last_message
def say_goodbye(_, context):
    return ((context.user_data['id'], 'Для того чтобы снова воспользоваться ботом, введите /start'),
            ConversationHandler.END)

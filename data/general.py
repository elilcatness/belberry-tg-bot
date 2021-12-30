from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ParseMode
from telegram.ext import ConversationHandler

from data.utils import delete_last_message, get_config


@delete_last_message
def start(update, context):
    cfg = get_config()
    buttons = [[InlineKeyboardButton('Информация и помощь', callback_data='info')],
               [InlineKeyboardButton('Сайт клиники', url=cfg.get('URL клиники', 'https://google.com'))],
               [InlineKeyboardButton('В другой раз...', callback_data='another_time')]]
    phone = cfg.get('Контактный номер телефона', 'Не указан')
    if len(phone.split(';')) > 1:
        phone = phone.split(';')[0]
    text = (f'Привет, %s!\n'
            f'Я буду твоим помощником в клинике <b>{cfg.get("Название клиники", "*")}</b>!\n'
            f'Также со мной можно связаться по номеру: {phone}')
    if update.message:
        context.user_data['id'] = update.message.from_user.id
        context.user_data['first_name'] = update.message.from_user.first_name
    if str(context.user_data['id']) in cfg.get('admins', []):
        buttons.extend([[InlineKeyboardButton(text='Изменить данные (admin)', callback_data='data')],
                        [InlineKeyboardButton(text='Сбросить настройки (admin)', callback_data='ask')]])
    if update.message:
        return update.message.reply_text(text % context.user_data['first_name'],
                                         reply_markup=InlineKeyboardMarkup(buttons),
                                         parse_mode=ParseMode.HTML), 'menu'
    return context.bot.send_message(context.user_data['id'], text % context.user_data['first_name'],
                                    reply_markup=InlineKeyboardMarkup(buttons),
                                    parse_mode=ParseMode.HTML), 'menu'


@delete_last_message
def ask_for_info_or_help(_, context):
    markup = InlineKeyboardMarkup(
        [[InlineKeyboardButton('Помощь', callback_data='help')],
         [InlineKeyboardButton('Информация', callback_data='info')],
         [InlineKeyboardButton('Вернуться назад', callback_data='back')]])
    return context.bot.send_message(context.user_data['id'], 'Вам нужна помощь или справочная информация?',
                                    reply_markup=markup), 'help_or_info'


@delete_last_message
def say_goodbye(_, context):
    return (context.bot.send_message(context.user_data['id'],
                                     'Для того чтобы снова воспользоваться ботом, введите /start'),
            ConversationHandler.END)
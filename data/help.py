from telegram import (ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove,
                      InlineKeyboardMarkup, InlineKeyboardButton, ParseMode)

from data.mail_sender import send_mail
from data.utils import delete_last_message, get_config


@delete_last_message
def help_menu(_, context):
    markup = InlineKeyboardMarkup(
        [[InlineKeyboardButton('Оставить отзыв', url=get_config().get('URL для отзыва', 'https://google.com'))],
         [InlineKeyboardButton('Записаться', callback_data='register')],
         [InlineKeyboardButton('Напомнить контакты', callback_data='contacts')],
         [InlineKeyboardButton('Консультация по телефону', callback_data='ask_phone')],
         [InlineKeyboardButton('Вернуться назад', callback_data='back')]])
    return (context.user_data['id'], 'Выберите опцию'), {'reply_markup': markup}, 'help_menu'


@delete_last_message
def show_contacts(_, context):
    cfg = get_config()
    markup = InlineKeyboardMarkup([[InlineKeyboardButton('Вернуться назад', callback_data='back')]])
    phone_key = 'Номер телефона'
    phone_data = cfg.get('Номер телефона', 'Не указан')
    if len(phone_data.split(';')) > 1:
        phone_data = '\n' + '\n'.join([f'• {ph}' for ph in phone_data.split(';')])
        phone_key = 'Номера телефонов'
    email_data = cfg.get('email', 'Не указан')
    if len(email_data.split(';')) > 1:
        email_data = '\n' + '\n'.join([f'• {mail}' for mail in email_data.split(';')])
    return ((context.user_data['id'], 'Я так рад, что Вы уже были у нас!\n\n'
                                      f'<b>{phone_key}:</b> {phone_data}\n'
                                      f'<b>E-mail:</b> {email_data}'),
            {'reply_markup': markup, 'parse_mode': ParseMode.HTML}, 'contacts')
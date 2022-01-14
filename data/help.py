from telegram import (ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove,
                      InlineKeyboardMarkup, InlineKeyboardButton, ParseMode)

from data.mail_sender import send_mail
from data.utils import handle_last_message, get_config


@handle_last_message
def help_menu(_, context):
    markup = InlineKeyboardMarkup(
        [[InlineKeyboardButton('Оставить отзыв', url=get_config().get('URL для отзыва', 'https://google.com'))],
         [InlineKeyboardButton('Записаться', callback_data='register')],
         [InlineKeyboardButton('Напомнить контакты', callback_data='contacts')],
         [InlineKeyboardButton('Консультация по телефону', callback_data='ask_phone')],
         [InlineKeyboardButton('Вернуться назад', callback_data='back')]])
    return (context.user_data['id'], 'Выберите опцию'), {'reply_markup': markup}, 'help_menu'


@handle_last_message
def show_contacts(_, context):
    cfg = get_config()
    markup = InlineKeyboardMarkup([[InlineKeyboardButton('Вернуться назад', callback_data='back')]])
    phone_key = 'Контактный номер телефона'
    phone_data = cfg.get('Контактный номер телефона', 'Не указан')
    if len(phone_data.split(';')) > 1:
        phone_data = '\n' + '\n'.join([f'• {ph}' for ph in phone_data.split(';')])
        phone_key = 'Контактные номера телефонов'
    email_data = cfg.get('email', 'Не указан')
    if len(email_data.split(';')) > 1:
        email_data = '\n' + '\n'.join([f'• {mail}' for mail in email_data.split(';')])
    return ((context.user_data['id'], 'Я так рад, что Вы уже были у нас!\n\n'
                                      f'<b>{phone_key}:</b> {phone_data}\n'
                                      f'<b>E-mail:</b> {email_data}'),
            {'reply_markup': markup, 'parse_mode': ParseMode.HTML}, 'contacts')


@handle_last_message
def ask_phone(_, context):
    markup = ReplyKeyboardMarkup([[KeyboardButton('Взять из Telegram', request_contact=True)],
                                  [KeyboardButton('Вернуться назад')]],
                                 resize_keyboard=True, one_time_keyboard=True)
    return ((context.user_data['id'], 'Я так рад, что Вы уже были у нас!\n\n'
                                      'Оставьте Ваш номер телефона, и мы перезвоним'),
            {'reply_markup': markup}, 'consult')


@handle_last_message
def consult(update, context):
    cfg = get_config()
    phone_number = (update.message.contact.phone_number
                    if getattr(update.message, 'contact')
                    and getattr(update.message.contact, 'phone_number') else update.message.text)
    markup = ReplyKeyboardRemove()
    email = cfg.get('email')
    if email and len(email.split(';')) > 1:
        email = email.split(';')[0]
    if not email or not send_mail(
            email, 'Заявка на консультацию',
            f'Заявка на консультацию поступила с указанием следующего номера: {phone_number}\n\n'
            f'<div align="right"><i>Уведомление было отправлено автоматически от Telegram бота '
            f'https://t.me/{context.bot.username}</i></div>'):
        update.message.reply_text('Произошла ошибка при создании заявки', reply_markup=markup)
    else:
        update.message.reply_text('Спасибо за заявку. Мы как можно скорее с Вами свяжемся',
                                  reply_markup=markup)
    return help_menu(update, context)

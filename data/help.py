from telegram import (ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove,
                      InlineKeyboardMarkup, InlineKeyboardButton, ParseMode)
from telegram.ext import CallbackContext

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
    return context.bot.send_message(context.user_data['id'], 'Выберите опцию',
                                    reply_markup=markup), 'help_menu'


@delete_last_message
def show_contacts(_, context):
    cfg = get_config()
    markup = InlineKeyboardMarkup([[InlineKeyboardButton('Вернуться назад', callback_data='back')]])
    return context.bot.send_message(
        context.user_data['id'],
        'Я так рад, что Вы уже были у нас!\n\n'
        f'<b>Контактный номер телефона:</b> {cfg.get("Контактный номер телефона", "Не указан")}\n'
        f'<b>E-mail:</b> {cfg.get("email", "Не указан")}',
        reply_markup=markup, parse_mode=ParseMode.HTML), 'contacts'


@delete_last_message
def ask_phone(_, context):
    markup = ReplyKeyboardMarkup([[KeyboardButton('Взять из Telegram', request_contact=True)],
                                  [KeyboardButton('Вернуться назад')]],
                                 resize_keyboard=True, one_time_keyboard=True)
    return context.bot.send_message(
        context.user_data['id'],
        'Я так рад, что Вы уже были у нас!\n\n'
        'Оставьте Ваш номер телефона, и мы перезвоним',
        reply_markup=markup), 'consult'


def consult(update, context):
    cfg = get_config()
    phone_number = (update.message.contact.phone_number
                    if getattr(update.message, 'contact')
                    and getattr(update.message.contact, 'phone_number') else update.message.text)
    markup = ReplyKeyboardRemove()
    if context.user_data.get('message_id'):
        context.bot.deleteMessage(context.user_data['id'], context.user_data.pop('message_id'))
    if not cfg.get('email') or not send_mail(
            cfg['email'], 'Заявка на консультацию',
            f'Заявка на консультацию поступила с указанием следующего номера: {phone_number}\n\n'
            f'<div align="right"><i>Уведомление было отправлено автоматически от Telegram бота '
            f'https://t.me/{context.bot.username}</i></div>'):
        update.message.reply_text('Произошла ошибка при создании заявки', reply_markup=markup)
    else:
        update.message.reply_text('Спасибо за заявку. Мы как можно скорее с Вами свяжемся',
                                  reply_markup=markup)
    return help_menu(update, context)

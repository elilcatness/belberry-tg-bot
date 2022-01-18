from telegram import InlineKeyboardMarkup, InlineKeyboardButton, ParseMode
from telegram.ext import CallbackContext

from data.utils import delete_last_message, get_config, clear_temp_vars


@delete_last_message
def help_menu(_, context: CallbackContext):
    clear_temp_vars(context)
    if context.user_data.get('specialist_id'):
        context.user_data.pop('specialist_id')
    if context.user_data.get('service_id'):
        context.user_data.pop('service_id')
    context.user_data['last_block'] = 'help'
    markup = InlineKeyboardMarkup(
        [[InlineKeyboardButton('Записаться на приём', callback_data='register')],
         [InlineKeyboardButton('Услуги', callback_data='services')],
         [InlineKeyboardButton('Специалисты', callback_data='specialists')],
         [InlineKeyboardButton('Оставить отзыв', callback_data='send_review')],
         [InlineKeyboardButton('Контакты', callback_data='contacts')],
         [InlineKeyboardButton('Узнать актуальные акции', callback_data='promotions')],
         [InlineKeyboardButton(
             'Перейти на сайт', url=get_config().get('URL клиники', dict()).get('val', 'https://belberry.net'))],
         [InlineKeyboardButton('Вернуться назад', callback_data='back')]])
    return context.bot.send_message(context.user_data['id'], 'Выберите опцию', reply_markup=markup), 'help_menu'


@delete_last_message
def show_contacts(_, context: CallbackContext):
    cfg = get_config()
    markup = InlineKeyboardMarkup([[InlineKeyboardButton('Вернуться назад', callback_data='back')]])
    phones = cfg.get('Номер телефона', {}).get('val', 'Не указан')
    if isinstance(phones, list) and len(phones) > 1:
        phone_key = 'Наши номера телефонов'
        phones = '\n' + '\n'.join([f'• {ph}' for ph in phones])
    else:
        phone_key = 'Наш номер телефона'
    e_mails = cfg.get('email', {}).get('val', 'Не указан')
    if isinstance(e_mails, list) and len(e_mails) > 1:
        e_mail_key = 'Наши E-mail'
        e_mails = '\n' + '\n'.join([f'• {e}' for e in e_mails])
    else:
        e_mail_key = 'Наш E-mail'
    return (context.bot.send_message(
        context.user_data['id'], '<b>Наши контакты:</b>\n\n'
                                 f'<b>{phone_key}:</b> {phones}\n'
                                 f'<b>{e_mail_key}:</b> {e_mails}',
        reply_markup=markup, parse_mode=ParseMode.HTML), 'help.contacts')


@delete_last_message
def ask_review(_, context: CallbackContext):
    markup = InlineKeyboardMarkup(
        [[InlineKeyboardButton('Вернуться назад', callback_data='back')],
         [InlineKeyboardButton(
             'Ссылка для отзыва (Яндекс.Карты)',
             url=get_config().get('URL для отзыва', {}).get('val', 'https://belberry.net'))],
         [InlineKeyboardButton('Отзыв отправлен', callback_data='review_sent')]])
    return context.bot.send_message(
        context.user_data['id'],
        'Для клиники очень важен каждый отзыв!\nНапишите свои пожелания.\nМы стараемся быть лучше',
        reply_markup=markup), 'help.ask_review'


@delete_last_message
def greet_for_review(_, context: CallbackContext):
    context.bot.send_message(context.user_data['id'], 'Спасибо, что написали отзыв!')
    return help_menu(_, context)

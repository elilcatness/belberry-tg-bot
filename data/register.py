from telegram import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove

from data.help import help_menu
from data.mail_sender import send_mail
from data.utils import delete_last_message, get_config, save_callback


def register_name(_, context):
    if context.user_data.get('message_id'):
        context.bot.deleteMessage(context.user_data['id'], context.user_data.pop('message_id'))
    if not get_config().get('email'):
        context.bot.send_message(
            context.user_data['id'],
            'Запись в данный момент недоступна из-за технических неполадок',
            reply_markup=ReplyKeyboardRemove())
        return help_menu(_, context)
    context.user_data['register'] = {}
    markup = ReplyKeyboardMarkup([[KeyboardButton('Вернуться назад')]], resize_keyboard=True)
    msg = context.bot.send_message(context.user_data['id'], 'Введите своё имя',
                                   reply_markup=markup)
    save_callback(context.user_data['id'], context.user_data['first_name'], 'register_name', msg.message_id)
    return 'register_name'


def register_phone(update, context):
    if context.user_data.get('message_id'):
        context.bot.deleteMessage(context.user_data['id'], context.user_data.pop('message_id'))
    context.user_data['register']['Имя'] = update.message.text
    markup = ReplyKeyboardMarkup([[KeyboardButton('Взять из Telegram', request_contact=True)],
                                  [KeyboardButton('Вернуться назад')]],
                                 resize_keyboard=True, one_time_keyboard=True)
    msg = context.bot.send_message(context.user_data['id'], 'Укажите свой номер телефона',
                                   reply_markup=markup)
    save_callback(context.user_data['id'], context.user_data['first_name'],
                  'register_phone', msg.message_id, register_name=update.message.text)
    return 'register_phone'


def finish_registration(update, context):
    context.user_data['register']['Номер телефона'] = (
        update.message.contact.phone_number
        if getattr(update.message, 'contact') and getattr(update.message.contact, 'phone_number')
        else update.message.text)
    markup = ReplyKeyboardRemove()
    if context.user_data.get('message'):
        context.user_data.pop('message').delete()
    if not send_mail(get_config().get('email'), 'Заявка на запись',
                     'Поступила заявка на запись со следующими данными:<br><br> '
                     '%s' % ('<br>'.join([f'<b>{key}</b>: {val}'
                                          for key, val in context.user_data['register'].items()]))
                     + f'<div align="right"><i>Уведомление было отправлено автоматически от Telegram бота '
                       f'https://t.me/{context.bot.username}</i></div>'):
        update.message.reply_text('Произошла ошибка при создании заявки', reply_markup=markup)
    else:
        update.message.reply_text('Ваша заявка была успешно отправлена. Ожидайте звонка')
    return help_menu(update, context)

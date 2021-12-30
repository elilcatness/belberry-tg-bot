from telegram import InlineKeyboardMarkup, InlineKeyboardButton, ParseMode

from data.utils import get_config, delete_last_message


@delete_last_message
def info_menu(_, context):
    markup = InlineKeyboardMarkup(
        [[InlineKeyboardButton('О нас', callback_data='about')],
         [InlineKeyboardButton(
             'Наши адреса' if len(get_config().get('Адрес клиники', '').split(';')) > 1
             else 'Наш адрес', callback_data='address')],
         [InlineKeyboardButton('Вернуться назад', callback_data='back')]])
    return context.bot.send_message(context.user_data['id'], 'Выберите тип информации',
                                    reply_markup=markup), 'info_menu'


@delete_last_message
def about(_, context):
    cfg = get_config()
    markup = InlineKeyboardMarkup([[InlineKeyboardButton('Вернуться назад', callback_data='back')]])
    phone_key = 'Наш телефон'
    phone = cfg.get('Номер телефона клиники', 'Не указан')
    if len(phone.split(';')) > 1:
        phone = '\n' + '\n'.join([f'• {ph}' for ph in phone.split(';')])
        phone_key = 'Наши телефоны'
    mail = cfg.get('email', 'Не указан')
    if len(mail.split(';')) > 1:
        mail = '\n' + '\n'.join([f'• {m}' for m in mail.split(';')])
    return context.bot.send_message(
        context.user_data['id'], f'{cfg.get("Описание клиники", "На данный момент описания нет")}\n\n'
                                 f'<b>{phone_key}:</b> {phone}\n\n'
                                 f'<b>E-Mail</b>: {mail}',
        reply_markup=markup, parse_mode=ParseMode.HTML), 'about_menu'


@delete_last_message
def show_address(_, context):
    markup = InlineKeyboardMarkup([[InlineKeyboardButton('Вернуться назад', callback_data='back')]])
    address_key = 'Наш адрес'
    address = get_config().get('Адрес клиники', 'Не указан')
    if len(address.split(';')) > 1:
        address = '\n' + '\n'.join([f'• {add}' for add in address.split(';')])
        address_key = 'Наши адреса'
    return context.bot.send_message(
        context.user_data['id'], f'<b>{address_key}:</b> {address}',
        reply_markup=markup, parse_mode=ParseMode.HTML), 'address_menu'

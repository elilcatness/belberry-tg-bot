from telegram import InlineKeyboardMarkup, InlineKeyboardButton, ParseMode

from data.utils import get_config, delete_last_message


@delete_last_message
def info_menu(_, context):
    markup = InlineKeyboardMarkup(
        [[InlineKeyboardButton('О нас', callback_data='about')],
         [InlineKeyboardButton('Наш адрес', callback_data='address')],
         [InlineKeyboardButton('Вернуться назад', callback_data='back')]])
    return context.bot.send_message(context.user_data['id'], 'Выберите тип информации',
                                    reply_markup=markup), 'info_menu'


@delete_last_message
def about(_, context):
    cfg = get_config()
    markup = InlineKeyboardMarkup([[InlineKeyboardButton('Вернуться назад', callback_data='back')]])
    return context.bot.send_message(
        context.user_data['id'], f'{cfg.get("Описание клиники", "На данный момент описания нет")}\n\n'
                                 f'<b>Наш телефон:</b> {cfg.get("Номер телефона клиники", "Не указан")}\n'
                                 f'<b>E-Mail</b>: {cfg.get("email", "Не указан")}',
        reply_markup=markup, parse_mode=ParseMode.HTML), 'about_menu'


@delete_last_message
def show_address(_, context):
    markup = InlineKeyboardMarkup([[InlineKeyboardButton('Вернуться назад', callback_data='back')]])
    return context.bot.send_message(
        context.user_data['id'], f'<b>Наш адрес:</b> {get_config().get("Адрес клиники", "Не указан")}',
        reply_markup=markup, parse_mode=ParseMode.HTML), 'address_menu'

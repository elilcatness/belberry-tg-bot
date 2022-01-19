from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ParseMode
from telegram.error import BadRequest
from telegram.ext import ConversationHandler, CallbackContext

from data.info import info_menu
from data.utils import delete_last_message, get_config, clear_temp_vars


@delete_last_message
def start(update, context):
    clear_temp_vars(context)
    if context.user_data.get('specialist_id'):
        context.user_data.pop('specialist_id')
    if context.user_data.get('service_id'):
        context.user_data.pop('service_id')
    if context.user_data.get('promotion_id'):
        context.user_data.pop('promotion_id')
    cfg = get_config()
    buttons = [
         [InlineKeyboardButton('Да', callback_data='help'), InlineKeyboardButton('Позже', callback_data='later')],
         [InlineKeyboardButton('Перейти на сайт', url=cfg.get('URL клиники', {}).get('val', 'https://belberry.net/'))]]
    phone = cfg.get('Номер телефона', {}).get('val', 'Не указан')
    if isinstance(phone, list) and len(phone) > 1:
        phone = phone[0]
    text = (f'Привет, %s! Я ассистент клиники <b>{cfg.get("Название клиники", {}).get("val", "*")}</b>.\n'
            f'Я помогу узнать про нашу клинику подробнее.\n'
            f'Могу быстро записать на приём к доктору.\n'
            f'А также буду напоминать о приёме, актуальных акциях и индивидуальных предложениях 😊\n\n'
            f'Также со мной можно связаться по телефону: {phone}\n\n'
            f'<b>Нужна ли Вам помощь?</b>')
    if update.message:
        context.user_data['id'] = update.message.from_user.id
        context.user_data['first_name'] = update.message.from_user.first_name
    if str(context.user_data['id']) in cfg.get('admins', {}).get('val', []):
        buttons.extend([[InlineKeyboardButton('Изменить данные (admin)', callback_data='data')],
                        [InlineKeyboardButton('Сбросить настройки (admin)', callback_data='ask')],
                        [InlineKeyboardButton('Добавить сущность (admin)', callback_data='add_menu')],
                        [InlineKeyboardButton('Редактировать сущность (admin)', callback_data='edit_menu')],
                        [InlineKeyboardButton('Удалить сущность (admin)', callback_data='delete_menu')]])
    if cfg.get("Фото клиники", {}).get('val'):
        try:
            return (context.bot.send_photo(context.user_data['id'], cfg["Фото клиники"]['val'],
                                           text % context.user_data['first_name'],
                                           reply_markup=InlineKeyboardMarkup(buttons), parse_mode=ParseMode.HTML),
                    'menu')
        except BadRequest:
            pass
    return (context.bot.send_message(context.user_data['id'], text % context.user_data['first_name'],
                                     reply_markup=InlineKeyboardMarkup(buttons), parse_mode=ParseMode.HTML),
            'menu')


@delete_last_message
def later(_, context: CallbackContext):
    context.bot.send_message(
        context.user_data['id'],
        f'Хорошо, {context.user_data["first_name"]}.\nЕсли Вы решите обратиться в нашу клинику, '
        f'Вы можете сделать это в данном чате')
    return info_menu(_, context)

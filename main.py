import json
import os

from dotenv import load_dotenv
from telegram.ext import (Updater, CommandHandler, ConversationHandler,
                          CallbackQueryHandler, MessageHandler, Filters)

from data.admin import *
from data.db import db_session
from data.help import *
from data.info import *
from data.register import *


@delete_last_message
def start(update: Update, context: CallbackContext):
    cfg = get_config()
    buttons = [[InlineKeyboardButton('Информация и помощь', callback_data='info')],
               [InlineKeyboardButton('Сайт клиники', url=cfg.get('URL клиники', 'https://google.com'))],
               [InlineKeyboardButton('В другой раз...', callback_data='another_time')]]
    text = (f'Привет, %s!\n'
            f'Я буду твоим помощником в клинике <b>{cfg.get("Название клиники", "*")}</b>!\n'
            f'Также со мной можно связаться по номеру: {cfg.get("Контактный номер телефона", "Не указан")}')
    user_id = update.message.from_user.id if update.message else context.user_data['user'].id
    if str(user_id) in cfg.get('admins', []):
        buttons.extend([[InlineKeyboardButton(text='Изменить данные (admin)', callback_data='data')],
                        [InlineKeyboardButton(text='Сбросить настройки (admin)', callback_data='ask')]])
    if update.message:
        context.user_data['user'] = update.message.from_user
        return update.message.reply_text(text % update.message.from_user.first_name,
                                         reply_markup=InlineKeyboardMarkup(buttons),
                                         parse_mode=ParseMode.HTML), 'menu'
    return context.bot.send_message(context.user_data['user'].id, text % context.user_data['user'].first_name,
                                    reply_markup=InlineKeyboardMarkup(buttons),
                                    parse_mode=ParseMode.HTML), 'menu'


@delete_last_message
def ask_for_info_or_help(_, context: CallbackContext):
    markup = InlineKeyboardMarkup(
        [[InlineKeyboardButton('Помощь', callback_data='help')],
         [InlineKeyboardButton('Информация', callback_data='info')],
         [InlineKeyboardButton('Вернуться назад', callback_data='back')]])
    return context.bot.send_message(context.user_data['user'].id, 'Вам нужна помощь или справочная информация?',
                                    reply_markup=markup), 'help_or_info'


@delete_last_message
def say_goodbye(_, context: CallbackContext):
    return (context.bot.send_message(context.user_data['user'].id,
                                     'Для того чтобы снова воспользоваться ботом, введите /start'),
            ConversationHandler.END)


def reset_data(update: Update, context):
    if context.user_data.get('message'):
        context.user_data.pop('message').delete()
    if update.message.text == 'Да':
        with open(os.path.join('data', 'config.json'), encoding='utf-8') as f:
            save_config(json.loads(f.read()))
            update.message.reply_text('Настройки были успешно сброшены')
    return start(update, context)


def main():
    updater = Updater(os.getenv('token'))
    updater.dispatcher.add_handler(ConversationHandler(
        allow_reentry=True,
        per_message=False,
        entry_points=[CommandHandler('start', start)],
        states={'menu': [CallbackQueryHandler(ask_for_info_or_help, pattern='info'),
                         CallbackQueryHandler(say_goodbye, pattern='another_time'),
                         CallbackQueryHandler(show_data, pattern='data'),
                         CallbackQueryHandler(ask_resetting_data, pattern='ask')],
                'data_resetting': [MessageHandler(Filters.regex('(Да)|(Нет)'), reset_data)],
                'data_requesting': [CallbackQueryHandler(start, pattern='menu'),
                                    CallbackQueryHandler(request_changing_data, pattern='')],
                'data': [CallbackQueryHandler(show_data, pattern='data'),
                         MessageHandler((~Filters.text('Вернуться назад')) & Filters.text, change_data)],
                'help_or_info': [CallbackQueryHandler(help_menu, pattern='help'),
                                 CallbackQueryHandler(info_menu, pattern='info'),
                                 CallbackQueryHandler(start, pattern='back')],
                'info_menu': [CallbackQueryHandler(about, pattern='about'),
                              CallbackQueryHandler(show_address, pattern='address'),
                              CallbackQueryHandler(ask_for_info_or_help, pattern='back')],
                'about_menu': [CallbackQueryHandler(info_menu, pattern='back')],
                'address_menu': [CallbackQueryHandler(info_menu, pattern='back')],
                'help_menu': [CallbackQueryHandler(register_name, pattern='register'),
                              CallbackQueryHandler(ask_phone, pattern='ask_phone'),
                              CallbackQueryHandler(show_contacts, pattern='contacts'),
                              CallbackQueryHandler(ask_for_info_or_help, pattern='back')],
                'contacts': [CallbackQueryHandler(help_menu, pattern='back')],
                'consult': [MessageHandler((~Filters.text('Вернуться назад')) & Filters.all, consult),
                            MessageHandler(Filters.text('Вернуться назад'), help_menu)],
                'register_name': [MessageHandler((~Filters.text('Вернуться назад')) & Filters.text,
                                                 register_phone),
                                  MessageHandler(Filters.text('Вернуться назад'), help_menu)],
                'register_phone': [MessageHandler((~Filters.text('Вернуться назад')) & Filters.all,
                                                  finish_registration),
                                   MessageHandler(Filters.text('Вернуться назад'), register_name)]},
        fallbacks=[CommandHandler('start', start)]
    ))
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    load_dotenv()
    db_session.global_init(os.getenv('DATABASE_URL'))
    main()

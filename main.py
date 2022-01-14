from dotenv import load_dotenv
from telegram.ext import (Updater, CommandHandler, ConversationHandler,
                          CallbackQueryHandler, MessageHandler, Filters)

from data.admin.panel import *
from data.db import db_session
from data.db.models.state import State
from data.general import ask_for_info_or_help, say_goodbye
from data.help import *
from data.info import *
from data.register import *


# Осторожно, костыль!!!!
def clear_keyboard(_, context):
    msg = context.bot.send_message(context.user_data['id'], '.', reply_markup=ReplyKeyboardRemove())
    msg.delete()
    return help_menu(_, context)


def load_states(updater: Updater, conv_handler: ConversationHandler):
    with db_session.create_session() as session:
        for state in session.query(State).all():
            conv_handler._conversations[(state.user_id, state.user_id)] = state.callback
            updater.dispatcher.user_data[state.user_id] = json.loads(state.data)


def main():
    updater = Updater(os.getenv('token'))
    conv_handler = ConversationHandler(
        allow_reentry=True,
        per_message=False,
        entry_points=[CommandHandler('start', start)],
        states={'menu': [CallbackQueryHandler(ask_for_info_or_help, pattern='info'),
                         CallbackQueryHandler(say_goodbye, pattern='another_time'),
                         CallbackQueryHandler(show_data, pattern='data'),
                         CallbackQueryHandler(ask_resetting_data, pattern='ask')],
                'data_resetting': [CallbackQueryHandler(reset_data, pattern='change_yes'),
                                   CallbackQueryHandler(start, pattern='change_no')],
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
                                  MessageHandler(Filters.text('Вернуться назад'), clear_keyboard)],
                'register_phone': [MessageHandler((~Filters.text('Вернуться назад')) & Filters.all,
                                                  finish_registration),
                                   MessageHandler(Filters.text('Вернуться назад'), register_name)]},
        fallbacks=[CommandHandler('start', start)])
    updater.dispatcher.add_handler(conv_handler)
    load_states(updater, conv_handler)
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    load_dotenv()
    db_session.global_init(os.getenv('DATABASE_URL'))
    main()

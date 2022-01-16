import cloudinary
from dotenv import load_dotenv
from telegram.ext import (Updater, CommandHandler, ConversationHandler,
                          CallbackQueryHandler, MessageHandler, Filters)

from data.admin.add import add_menu, SpecialistAddition, ServiceAddition
from data.admin.panel import *
from data.db import db_session
from data.db.models.state import State
from data.general import ask_for_help_menu, say_goodbye
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
        states={'menu': [CallbackQueryHandler(ask_for_help_menu, pattern='help'),
                         CallbackQueryHandler(say_goodbye, pattern='another_time'),
                         CallbackQueryHandler(show_data, pattern='data'),
                         CallbackQueryHandler(ask_resetting_data, pattern='ask'),
                         CallbackQueryHandler(add_menu, pattern='add_menu')],
                'admin.data_resetting': [CallbackQueryHandler(reset_data, pattern='change_yes'),
                                         CallbackQueryHandler(start, pattern='change_no')],
                'admin.data_requesting': [CallbackQueryHandler(start, pattern='menu'),
                                          CallbackQueryHandler(request_changing_data, pattern='')],
                'admin.data': [CallbackQueryHandler(show_data, pattern='data'),
                               MessageHandler((~Filters.text('Вернуться назад')) & Filters.text, change_data)],
                'add_menu': [CallbackQueryHandler(SpecialistAddition.ask_full_name, pattern='add_specialists'),
                             CallbackQueryHandler(ServiceAddition.ask_name, pattern='add_services'),
                             CallbackQueryHandler(start, pattern='back')],
                'SpecialistAddition.ask_full_name': [
                    MessageHandler(Filters.text, SpecialistAddition.ask_speciality),
                    CallbackQueryHandler(add_menu, pattern='back')],
                'SpecialistAddition.ask_speciality': [
                    MessageHandler(Filters.text, SpecialistAddition.ask_description),
                    CallbackQueryHandler(SpecialistAddition.ask_full_name, pattern='back')],
                'SpecialistAddition.ask_description': [
                    MessageHandler(Filters.text, SpecialistAddition.ask_photo),
                    CallbackQueryHandler(SpecialistAddition.ask_photo, pattern='skip_description'),
                    CallbackQueryHandler(SpecialistAddition.ask_speciality, pattern='back')],
                'SpecialistAddition.ask_photo': [
                    MessageHandler(Filters.photo | Filters.document, SpecialistAddition.finish),
                    CallbackQueryHandler(SpecialistAddition.finish, pattern='skip_photo'),
                    CallbackQueryHandler(SpecialistAddition.ask_description, pattern='back')],
                'ServiceAddition.ask_name': [
                    MessageHandler(Filters.text, ServiceAddition.ask_description),
                    CallbackQueryHandler(add_menu, pattern='back')],
                'ServiceAddition.ask_description': [
                    MessageHandler(Filters.text, ServiceAddition.ask_photo),
                    CallbackQueryHandler(ServiceAddition.ask_photo, pattern='skip_description'),
                    CallbackQueryHandler(ServiceAddition.ask_name, pattern='back')],
                'ServiceAddition.ask_photo': [
                    MessageHandler(Filters.photo | Filters.document, ServiceAddition.finish),
                    CallbackQueryHandler(ServiceAddition.finish, pattern='skip_photo'),
                    CallbackQueryHandler(ServiceAddition.ask_description, pattern='back')],
                'ask_for_help': [CallbackQueryHandler(help_menu, pattern='yes'),
                                 CallbackQueryHandler(info_menu, pattern='no'),
                                 CallbackQueryHandler(start, pattern='back')],
                'info_menu': [CallbackQueryHandler(about, pattern='about'),
                              CallbackQueryHandler(show_address, pattern='address'),
                              CallbackQueryHandler(show_socials, pattern='socials'),
                              CallbackQueryHandler(ask_for_help_menu, pattern='back')],
                'about_menu': [CallbackQueryHandler(info_menu, pattern='back')],
                'address_menu': [CallbackQueryHandler(choose_route_engine, pattern='route'),
                                 CallbackQueryHandler(info_menu, pattern='back')],
                'route_menu': [CallbackQueryHandler(show_address, pattern='back')],
                'socials_menu': [CallbackQueryHandler(info_menu, pattern='back')],
                'help_menu': [CallbackQueryHandler(register_name, pattern='register'),
                              CallbackQueryHandler(ask_phone, pattern='ask_phone'),
                              CallbackQueryHandler(show_contacts, pattern='contacts'),
                              CallbackQueryHandler(ask_for_help_menu, pattern='back')],
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
    cfg = get_config()
    cloudinary.config(
        cloud_name=cfg['cloudinary.cloud_name'],
        api_key=cfg['cloudinary.api_key'],
        api_secret=cfg['cloudinary.api_secret'])
    main()

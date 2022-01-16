import json
import os

import cloudinary
from dotenv import load_dotenv
from telegram import ReplyKeyboardRemove
from telegram.ext import (Updater, CommandHandler, ConversationHandler,
                          CallbackQueryHandler, MessageHandler, Filters)

from data.admin.add import add_menu, SpecialistAddition, ServiceAddition
from data.admin.delete import SpecialistDelete, ServiceDelete, delete_menu
from data.admin.edit import SpecialistEdit, edit_menu, ServiceEdit
from data.admin.panel import show_data, reset_data, ask_resetting_data, request_changing_data, change_data
from data.consult import Consult
from data.db import db_session
from data.db.models.state import State
from data.general import ask_for_help_menu, later, start
from data.help import help_menu, ask_review, greet_for_review, show_contacts
from data.info import info_menu, show_address, show_socials, about, choose_route_engine
from data.register import Register
from data.utils import get_config
from data.view import SpecialistViewPublic, ServiceViewPublic


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
                         CallbackQueryHandler(later, pattern='later'),
                         CallbackQueryHandler(show_data, pattern='data'),
                         CallbackQueryHandler(ask_resetting_data, pattern='ask'),
                         CallbackQueryHandler(add_menu, pattern='add_menu'),
                         CallbackQueryHandler(edit_menu, pattern='edit_menu'),
                         CallbackQueryHandler(delete_menu, pattern='delete_menu')],
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
                    MessageHandler(Filters.text, SpecialistAddition.ask_services),
                    CallbackQueryHandler(SpecialistAddition.ask_services, pattern='skip_description'),
                    CallbackQueryHandler(SpecialistAddition.ask_speciality, pattern='back')],
                'SpecialistAddition.services.show_all': [
                    CallbackQueryHandler(SpecialistAddition.handle_service_selection, pattern='[0-9]+'),
                    CallbackQueryHandler(ServiceViewPublic.set_next_page, pattern='next_page'),
                    CallbackQueryHandler(ServiceViewPublic.show_all, pattern='refresh'),
                    CallbackQueryHandler(ServiceViewPublic.set_previous_page, pattern='prev_page'),
                    MessageHandler(Filters.regex(r'[0-9]+'), ServiceViewPublic.set_page),
                    CallbackQueryHandler(SpecialistAddition.ask_photo, pattern='next'),
                    CallbackQueryHandler(SpecialistAddition.ask_description, pattern='back')
                ],
                'SpecialistAddition.ask_photo': [
                    MessageHandler(Filters.photo | Filters.document, SpecialistAddition.finish),
                    CallbackQueryHandler(SpecialistAddition.finish, pattern='skip_photo'),
                    CallbackQueryHandler(SpecialistAddition.ask_services, pattern='back')],
                'ServiceAddition.ask_name': [
                    MessageHandler(Filters.text, ServiceAddition.ask_description),
                    CallbackQueryHandler(add_menu, pattern='back')],
                'ServiceAddition.ask_description': [
                    MessageHandler(Filters.text, ServiceAddition.ask_specialists),
                    CallbackQueryHandler(ServiceAddition.ask_specialists, pattern='skip_description'),
                    CallbackQueryHandler(ServiceAddition.ask_name, pattern='back')],
                'ServiceAddition.specialists.show_all': [
                    CallbackQueryHandler(ServiceAddition.handle_specialist_selection, pattern='[0-9]+ action'),
                    CallbackQueryHandler(SpecialistViewPublic.set_next_page, pattern='next_page'),
                    CallbackQueryHandler(SpecialistViewPublic.show_all, pattern='refresh'),
                    CallbackQueryHandler(SpecialistViewPublic.set_previous_page, pattern='prev_page'),
                    MessageHandler(Filters.regex(r'[0-9]+'), SpecialistViewPublic.set_page),
                    CallbackQueryHandler(ServiceAddition.ask_photo, pattern='next'),
                    CallbackQueryHandler(ServiceAddition.ask_photo, pattern='skip_specialists'),
                    CallbackQueryHandler(ServiceAddition.ask_description, pattern='back')],
                'ServiceAddition.ask_photo': [
                    MessageHandler(Filters.photo | Filters.document, ServiceAddition.finish),
                    CallbackQueryHandler(ServiceAddition.finish, pattern='skip_photo'),
                    CallbackQueryHandler(ServiceAddition.ask_specialists, pattern='back')],
                'edit_menu': [CallbackQueryHandler(SpecialistEdit.show_all, pattern='edit_specialists'),
                              CallbackQueryHandler(ServiceEdit.show_all, pattern='edit_services'),
                              CallbackQueryHandler(start, pattern='back')],
                'edit.services.show_all': [
                    CallbackQueryHandler(ServiceEdit.edit_menu, pattern='[0-9]+ action'),
                    CallbackQueryHandler(ServiceViewPublic.set_next_page, pattern='next_page'),
                    CallbackQueryHandler(ServiceViewPublic.show_all, pattern='refresh'),
                    CallbackQueryHandler(ServiceViewPublic.set_previous_page, pattern='prev_page'),
                    MessageHandler(Filters.regex(r'[0-9]+'), ServiceViewPublic.set_page),
                    CallbackQueryHandler(edit_menu, pattern='back')],
                'edit.services.specialists.show_all': [
                    CallbackQueryHandler(ServiceEdit.handle_specialist_selection, pattern='[0-9]+'),
                    CallbackQueryHandler(SpecialistViewPublic.set_next_page, pattern='next_page'),
                    CallbackQueryHandler(SpecialistViewPublic.show_all, pattern='refresh'),
                    CallbackQueryHandler(SpecialistViewPublic.set_previous_page, pattern='prev_page'),
                    MessageHandler(Filters.regex(r'[0-9]+'), SpecialistViewPublic.set_page),
                    CallbackQueryHandler(ServiceEdit.save_specialists, pattern='next'),
                    CallbackQueryHandler(ServiceEdit.edit_menu, pattern='back')
                ],
                'edit.services.edit_menu': [
                    CallbackQueryHandler(ServiceEdit.show_all, pattern='back'),
                    CallbackQueryHandler(ServiceEdit.show_specialists, pattern='specialists'),
                    CallbackQueryHandler(ServiceEdit.ask_new_value, pattern='.*')
                ],
                'edit.services.ask_new_value': [
                    MessageHandler(Filters.text | Filters.photo, ServiceEdit.set_new_value),
                    CallbackQueryHandler(ServiceEdit.edit_menu, pattern='back')
                ],
                'edit.specialists.show_all': [
                    CallbackQueryHandler(SpecialistEdit.edit_menu, pattern='[0-9]+ action'),
                    CallbackQueryHandler(SpecialistViewPublic.set_next_page, pattern='next_page'),
                    CallbackQueryHandler(SpecialistViewPublic.show_all, pattern='refresh'),
                    CallbackQueryHandler(SpecialistViewPublic.set_previous_page, pattern='prev_page'),
                    MessageHandler(Filters.regex(r'[0-9]+'), SpecialistViewPublic.set_page),
                    CallbackQueryHandler(edit_menu, pattern='back')],
                'edit.specialists.services.show_all': [
                    CallbackQueryHandler(SpecialistEdit.handle_service_selection, pattern='[0-9]+'),
                    CallbackQueryHandler(ServiceViewPublic.set_next_page, pattern='next_page'),
                    CallbackQueryHandler(ServiceViewPublic.show_all, pattern='refresh'),
                    CallbackQueryHandler(ServiceViewPublic.set_previous_page, pattern='prev_page'),
                    MessageHandler(Filters.regex(r'[0-9]+'), ServiceViewPublic.set_page),
                    CallbackQueryHandler(SpecialistEdit.save_services, pattern='next'),
                    CallbackQueryHandler(SpecialistEdit.edit_menu, pattern='back')
                ],
                'edit.specialists.edit_menu': [
                    CallbackQueryHandler(SpecialistEdit.show_all, pattern='back'),
                    CallbackQueryHandler(SpecialistEdit.show_services, pattern='services'),
                    CallbackQueryHandler(SpecialistEdit.ask_new_value, pattern='.*')
                ],
                'edit.specialists.ask_new_value': [
                    MessageHandler(Filters.text | Filters.photo, SpecialistEdit.set_new_value),
                    CallbackQueryHandler(SpecialistEdit.edit_menu, pattern='back')
                ],
                'delete_menu': [CallbackQueryHandler(SpecialistDelete.show_all, pattern='delete_specialists'),
                                CallbackQueryHandler(ServiceDelete.show_all, pattern='delete_services'),
                                CallbackQueryHandler(start, pattern='back')],
                'delete.specialists.show_all': [
                    CallbackQueryHandler(SpecialistDelete.confirm, pattern='[0-9]+ action'),
                    CallbackQueryHandler(SpecialistViewPublic.set_next_page, pattern='next_page'),
                    CallbackQueryHandler(SpecialistViewPublic.show_all, pattern='refresh'),
                    CallbackQueryHandler(SpecialistViewPublic.set_previous_page, pattern='prev_page'),
                    MessageHandler(Filters.regex(r'[0-9]+'), SpecialistViewPublic.set_page),
                    CallbackQueryHandler(delete_menu, pattern='back')],
                'delete.specialists.confirm': [
                    CallbackQueryHandler(SpecialistDelete.delete, pattern='confirmed'),
                    CallbackQueryHandler(SpecialistDelete.show_all, pattern='back')],
                'delete.services.show_all': [
                    CallbackQueryHandler(ServiceDelete.confirm, pattern='[0-9]+ action'),
                    CallbackQueryHandler(SpecialistViewPublic.set_next_page, pattern='next_page'),
                    CallbackQueryHandler(SpecialistViewPublic.show_all, pattern='refresh'),
                    CallbackQueryHandler(SpecialistViewPublic.set_previous_page, pattern='prev_page'),
                    MessageHandler(Filters.regex(r'[0-9]+'), SpecialistViewPublic.set_page),
                    CallbackQueryHandler(delete_menu, pattern='back')],
                'delete.services.confirm': [
                    CallbackQueryHandler(ServiceDelete.delete, pattern='confirmed'),
                    CallbackQueryHandler(ServiceDelete.show_all, pattern='back')],
                'ask_for_help': [CallbackQueryHandler(help_menu, pattern='yes'),
                                 CallbackQueryHandler(info_menu, pattern='no'),
                                 CallbackQueryHandler(start, pattern='back')],
                'info_menu': [CallbackQueryHandler(SpecialistViewPublic.show_all, pattern='specialists'),
                              CallbackQueryHandler(ServiceViewPublic.show_all, pattern='services'),
                              CallbackQueryHandler(about, pattern='about'),
                              CallbackQueryHandler(show_address, pattern='address'),
                              CallbackQueryHandler(show_socials, pattern='socials'),
                              CallbackQueryHandler(ask_for_help_menu, pattern='back')],
                'info.specialists.show_all': [
                    CallbackQueryHandler(SpecialistViewPublic.register, pattern='[0-9]+ action'),
                    CallbackQueryHandler(SpecialistViewPublic.show_services, pattern='[0-9]+'),
                    CallbackQueryHandler(SpecialistViewPublic.set_next_page, pattern='next_page'),
                    CallbackQueryHandler(SpecialistViewPublic.show_all, pattern='refresh'),
                    CallbackQueryHandler(SpecialistViewPublic.set_previous_page, pattern='prev_page'),
                    MessageHandler(Filters.regex(r'[0-9]+'), SpecialistViewPublic.set_page),
                    CallbackQueryHandler(info_menu, pattern='back')],
                'info.specialists.register_name': [
                    MessageHandler((~Filters.text('Вернуться назад')) & Filters.text, Register.register_phone),
                    MessageHandler(Filters.text('Вернуться назад'), SpecialistViewPublic.show_all)],
                'info.specialists.register_phone': [
                    MessageHandler((~Filters.text('Вернуться назад')) & Filters.all, Register.finish),
                    MessageHandler(Filters.text('Вернуться назад'), Register.register_name)
                ],
                'info.specialists.services.show_all': [
                    CallbackQueryHandler(ServiceViewPublic.register, pattern='[0-9]* action'),
                    CallbackQueryHandler(ServiceViewPublic.set_next_page, pattern='next_page'),
                    CallbackQueryHandler(ServiceViewPublic.show_all, pattern='refresh'),
                    CallbackQueryHandler(ServiceViewPublic.set_previous_page, pattern='prev_page'),
                    MessageHandler(Filters.regex(r'[0-9]+'), ServiceViewPublic.set_page),
                    CallbackQueryHandler(SpecialistViewPublic.show_all, pattern='back')
                ],
                'info.specialists.services.register_name': [
                    MessageHandler((~Filters.text('Вернуться назад')) & Filters.text, Register.register_phone),
                    MessageHandler(Filters.text('Вернуться назад'), ServiceViewPublic.show_all)],
                'info.specialists.services.register_phone': [
                    MessageHandler((~Filters.text('Вернуться назад')) & Filters.all, Register.finish),
                    MessageHandler(Filters.text('Вернуться назад'), Register.register_name)
                ],
                'info.services.show_all': [
                    CallbackQueryHandler(ServiceViewPublic.register, pattern='[0-9]* action'),
                    CallbackQueryHandler(ServiceViewPublic.show_specialists, pattern='[0-9]+'),
                    CallbackQueryHandler(ServiceViewPublic.set_next_page, pattern='next_page'),
                    CallbackQueryHandler(ServiceViewPublic.show_all, pattern='refresh'),
                    CallbackQueryHandler(ServiceViewPublic.set_previous_page, pattern='prev_page'),
                    MessageHandler(Filters.regex(r'[0-9]+'), ServiceViewPublic.set_page),
                    CallbackQueryHandler(info_menu, pattern='back')],
                'info.services.register_name': [
                    MessageHandler((~Filters.text('Вернуться назад')) & Filters.text, Register.register_phone),
                    MessageHandler(Filters.text('Вернуться назад'), ServiceViewPublic.show_all)],
                'info.services.register_phone': [
                    MessageHandler((~Filters.text('Вернуться назад')) & Filters.all, Register.finish),
                    MessageHandler(Filters.text('Вернуться назад'), Register.register_name)
                ],
                'info.services.specialists.show_all': [
                    CallbackQueryHandler(SpecialistViewPublic.register, pattern='[0-9]+ action'),
                    CallbackQueryHandler(SpecialistViewPublic.show_services, pattern='[0-9]+'),
                    CallbackQueryHandler(SpecialistViewPublic.set_next_page, pattern='next_page'),
                    CallbackQueryHandler(SpecialistViewPublic.show_all, pattern='refresh'),
                    CallbackQueryHandler(SpecialistViewPublic.set_previous_page, pattern='prev_page'),
                    MessageHandler(Filters.regex(r'[0-9]+'), SpecialistViewPublic.set_page),
                    CallbackQueryHandler(ServiceViewPublic.show_all, pattern='back')],
                'info.services.specialists.register_name': [
                    MessageHandler((~Filters.text('Вернуться назад')) & Filters.text, Register.register_phone),
                    MessageHandler(Filters.text('Вернуться назад'), SpecialistViewPublic.show_all)],
                'info.services.specialists.register_phone': [
                    MessageHandler((~Filters.text('Вернуться назад')) & Filters.all, Register.finish),
                    MessageHandler(Filters.text('Вернуться назад'), Register.register_name)
                ],
                'about_menu': [CallbackQueryHandler(info_menu, pattern='back'),
                               CallbackQueryHandler(Consult.ask_phone, pattern='consult')],
                'about.consult': [MessageHandler((~Filters.text('Вернуться назад')) & Filters.all, Consult.finish),
                                  MessageHandler(Filters.text('Вернуться назад'), about)],
                'address_menu': [CallbackQueryHandler(choose_route_engine, pattern='route'),
                                 CallbackQueryHandler(info_menu, pattern='back')],
                'route_menu': [CallbackQueryHandler(show_address, pattern='back')],
                'socials_menu': [CallbackQueryHandler(info_menu, pattern='back')],
                'help_menu': [CallbackQueryHandler(Register.register_name, pattern='register'),
                              CallbackQueryHandler(ask_review, pattern='send_review'),
                              CallbackQueryHandler(show_contacts, pattern='contacts'),
                              CallbackQueryHandler(ask_for_help_menu, pattern='back')],
                'help.ask_review': [CallbackQueryHandler(greet_for_review, pattern='review_sent'),
                                    CallbackQueryHandler(help_menu, pattern='back')],
                'help.contacts': [CallbackQueryHandler(help_menu, pattern='back')],
                'help.register_name': [
                    MessageHandler((~Filters.text('Вернуться назад')) & Filters.text, Register.register_phone),
                    MessageHandler(Filters.text('Вернуться назад'), help_menu)],
                'help.register_phone': [
                    MessageHandler((~Filters.text('Вернуться назад')) & Filters.all, Register.finish),
                    MessageHandler(Filters.text('Вернуться назад'), Register.register_name)],
                },
        # 'help_menu': [CallbackQueryHandler(register_name, pattern='register'),
        #               CallbackQueryHandler(ask_phone, pattern='ask_phone'),
        #               CallbackQueryHandler(show_contacts, pattern='contacts'),
        #               CallbackQueryHandler(ask_for_help_menu, pattern='back')],
        # 'contacts': [CallbackQueryHandler(help_menu, pattern='back')],

        # 'register_phone': [MessageHandler((~Filters.text('Вернуться назад')) & Filters.all,
        #                                   finish_registration),
        #                    MessageHandler(Filters.text('Вернуться назад'), register_name)]},
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
        cloud_name=cfg['cloudinary.cloud_name']['val'],
        api_key=cfg['cloudinary.api_key']['val'],
        api_secret=cfg['cloudinary.api_secret']['val'])
    main()

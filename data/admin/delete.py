from telegram import InlineKeyboardMarkup, InlineKeyboardButton, ParseMode
from telegram.ext import CallbackContext

from data.db import db_session
from data.db.models.service import Service
from data.db.models.specialist import Specialist
from data.utils import delete_last_message, clear_temp_vars
from data.view import SpecialistViewPublic, ServiceViewPublic


@delete_last_message
def delete_menu(_, context: CallbackContext):
    clear_temp_vars(context)
    if context.user_data.get('specialist_id'):
        context.user_data.pop('specialist_id')
    if context.user_data.get('service_id'):
        context.user_data.pop('service_id')
    context.user_data['last_block'] = 'delete'
    markup = InlineKeyboardMarkup([[InlineKeyboardButton('Специалист', callback_data='delete_specialists')],
                                   [InlineKeyboardButton('Услуга', callback_data='delete_services')],
                                   [InlineKeyboardButton('Вернуться назад', callback_data='back')]])
    return (context.bot.send_message(context.user_data['id'], 'Выберите сущность для удаления',
                                     reply_markup=markup), 'delete_menu')


class SpecialistDelete:
    @staticmethod
    @delete_last_message
    def show_all(_, context: CallbackContext, is_sub_already=True):
        context.user_data['action_text'] = 'Удалить'
        SpecialistViewPublic.show_all(_, context, is_sub_already=is_sub_already)
        return 'delete.specialists.show_all'

    @staticmethod
    @delete_last_message
    def confirm(_, context: CallbackContext):
        context.user_data['specialist_id'] = int(context.match.string.split()[0])
        markup = InlineKeyboardMarkup([[InlineKeyboardButton('Да', callback_data='confirmed')],
                                       [InlineKeyboardButton('Вернуться назад', callback_data='back')]])
        with db_session.create_session() as session:
            spec = session.query(Specialist).get(context.user_data['specialist_id'])
            return (context.bot.send_message(
                context.user_data['id'],
                f'Вы уверены, что хотите удалить специалиста '
                f'<b>{spec.speciality} {spec.full_name}</b>?',
                reply_markup=markup, parse_mode=ParseMode.HTML), 'delete.specialists.confirm')

    @staticmethod
    @delete_last_message
    def delete(_, context: CallbackContext):
        with db_session.create_session() as session:
            spec = session.query(Specialist).get(context.user_data.pop('specialist_id'))
            speciality, full_name = spec.speciality, spec.full_name
            session.delete(spec)
            session.commit()
            context.bot.send_message(
                context.user_data['id'],
                f'Специалист <b>{speciality} {full_name}</b> был успешно удалён',
                parse_mode=ParseMode.HTML)
            return SpecialistDelete.show_all(_, context)


class ServiceDelete:
    @staticmethod
    @delete_last_message
    def show_all(_, context: CallbackContext, is_sub_already=True):
        context.user_data['action_text'] = 'Удалить'
        ServiceViewPublic.show_all(_, context, is_sub_already=is_sub_already)
        return 'delete.services.show_all'

    @staticmethod
    @delete_last_message
    def confirm(_, context: CallbackContext):
        context.user_data['service_id'] = int(context.match.string.split()[0])
        markup = InlineKeyboardMarkup([[InlineKeyboardButton('Да', callback_data='confirmed')],
                                       [InlineKeyboardButton('Вернуться назад', callback_data='back')]])
        with db_session.create_session() as session:
            service = session.query(Service).get(context.user_data['service_id'])
            return (context.bot.send_message(
                context.user_data['id'],
                f'Вы уверены, что хотите удалить услугу <b>{service.name}</b>?',
                reply_markup=markup, parse_mode=ParseMode.HTML), 'delete.services.confirm')

    @staticmethod
    @delete_last_message
    def delete(_, context: CallbackContext):
        with db_session.create_session() as session:
            service = session.query(Service).get(context.user_data.pop('service_id'))
            name = service.name
            session.delete(service)
            session.commit()
            context.bot.send_message(
                context.user_data['id'],
                f'Услуга <b>{name}</b> была успешно удалена',
                parse_mode=ParseMode.HTML)
            return ServiceDelete.show_all(_, context)
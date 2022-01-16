from telegram.ext import CallbackContext

from data.constants import PAGINATION_STEP
from data.db import db_session
from data.db.models.specialist import Specialist
from data.utils import delete_last_message, build_pagination
from data.register import Register


class SpecialistViewPublic:
    @staticmethod
    @delete_last_message
    def show_all(_, context: CallbackContext):
        with db_session.create_session() as session:
            specialists = [spec.to_dict() for spec in session.query(Specialist).all()]
        if not context.user_data.get('spec_pagination'):
            context.user_data['spec_pagination'] = 1
        context.user_data['spec_pages_count'] = build_pagination(
            context, specialists, PAGINATION_STEP, context.user_data['spec_pagination'],
            ('специалист', 'специалиста', 'специалистов'),
            'Услуги', 'services')
        return (f'{context.user_data["last_block"]}.specialists.show_all'
                if 'specialists' not in context.user_data['last_block']
                else f'{context.user_data["last_block"]}.show_all')

    @staticmethod
    def set_next_page(_, context):
        context.user_data['spec_pagination'] += 1
        return SpecialistViewPublic.show_all(_, context)

    @staticmethod
    def set_previous_page(_, context):
        context.user_data['spec_pagination'] -= 1
        return SpecialistViewPublic.show_all(_, context)

    @staticmethod
    def set_page(update, context):
        n = int(update.message.text)
        if not (1 <= n <= context.user_data['spec_pages_count']):
            update.message.reply_text('Введён неверный номер страницы')
        else:
            context.user_data['spec_pagination'] = n
        return SpecialistViewPublic.show_all(update, context)

    @staticmethod
    def register(update, context: CallbackContext):
        if 'specialists' not in context.user_data['last_block']:
            context.user_data['last_block'] = f'{context.user_data["last_block"]}.specialists'
        return Register.register_name(update, context)

from telegram.ext import CallbackContext

from data.constants import PAGINATION_STEP
from data.db import db_session
from data.db.models.promotion import Promotion
from data.db.models.service import Service
from data.db.models.specialist import Specialist
from data.utils import delete_last_message, build_pagination, process_view, terminate_jobs
from data.register import Register


class SpecialistViewPublic:
    @staticmethod
    @delete_last_message
    def show_all(_, context: CallbackContext, is_sub_already=False, _filter=True):
        if not is_sub_already:
            context.user_data['specialists.is_sub_already'] = False
        if ('specialists' in context.user_data.get('last_block', '')
                and not context.user_data.get('last_block', '').endswith('specialists')):
            context.user_data['last_block'] = f'{context.user_data["last_block"].split(".")[0]}.specialists'
        job_name = f'process {context.user_data["id"]}'
        context.user_data['process.msg_text'] = 'Подождите. Данные загружаются'
        context.job_queue.run_repeating(process_view, 1, 0,
                                        context=context, name=job_name)
        if context.user_data.get('specialist_id'):
            context.user_data.pop('specialist_id')
        if not is_sub_already and context.user_data.get('found_suffix'):
            context.user_data.pop('found_suffix')
        with db_session.create_session() as session:
            if context.user_data.get('service_id') and _filter:
                service = session.query(Service).get(context.user_data['service_id'])
                context.user_data['found_suffix'] = f'. Услуга: <b>{service.name}</b>'
                specialists = [spec.to_dict() for spec in session.query(Specialist).all()
                               if service in spec.services]
            else:
                specialists = [spec.to_dict() for spec in session.query(Specialist).all()]
        if not context.user_data.get('spec_pagination'):
            context.user_data['spec_pagination'] = 1
        context.user_data['spec_pages_count'] = build_pagination(
            context, specialists, PAGINATION_STEP, context.user_data['spec_pagination'],
            ('специалист', 'специалиста', 'специалистов'), 'Услуги',
            context.user_data.get('specialists.is_sub_already', True))
        terminate_jobs(context, job_name)
        return (f'{context.user_data["last_block"]}.specialists.show_all'
                if 'specialists' not in context.user_data['last_block']
                else f'{context.user_data["last_block"]}.show_all')

    @staticmethod
    def set_next_page(_, context):
        context.user_data['spec_pagination'] += 1
        return SpecialistViewPublic.show_all(
            _, context, is_sub_already=context.user_data.get('specialists.is_sub_already', False))

    @staticmethod
    def set_previous_page(_, context):
        context.user_data['spec_pagination'] -= 1
        return SpecialistViewPublic.show_all(
            _, context, is_sub_already=context.user_data.get('specialists.is_sub_already', False))

    @staticmethod
    def set_page(update, context):
        n = int(update.message.text)
        if not (1 <= n <= context.user_data['spec_pages_count']):
            update.message.reply_text('Введён неверный номер страницы')
        else:
            context.user_data['spec_pagination'] = n
        return SpecialistViewPublic.show_all(
            update, context, is_sub_already=context.user_data.get('specialists.is_sub_already', False))

    @staticmethod
    def register(update, context: CallbackContext):
        if 'specialists' not in context.user_data['last_block']:
            context.user_data['last_block'] = f'{context.user_data["last_block"]}.specialists'
        return Register.register_name(update, context)

    @staticmethod
    @delete_last_message
    def show_services(_, context: CallbackContext):
        context.user_data['specialist_id'] = int(context.match.string)
        if 'specialists' not in context.user_data['last_block']:
            context.user_data['last_block'] = f'{context.user_data["last_block"]}.specialists'
        context.user_data['services.is_sub_already'] = True
        return ServiceViewPublic.show_all(_, context, is_sub_already=True)


class ServiceViewPublic:
    @staticmethod
    @delete_last_message
    def show_all(_, context: CallbackContext, is_sub_already: bool = False, _filter: bool = True):
        if ('services' in context.user_data.get('last_block', '')
                and not context.user_data.get('last_block', '').endswith('services')):
            context.user_data['last_block'] = f'{context.user_data["last_block"].split(".")[0]}.services'
        if not is_sub_already:
            context.user_data['services.is_sub_already'] = False
        if context.user_data.get('service_id'):
            context.user_data.pop('service_id')
        if not is_sub_already and context.user_data.get('found_suffix'):
            context.user_data.pop('found_suffix')
        with db_session.create_session() as session:
            if context.user_data.get('promotion_id') and _filter:
                promotion = session.query(Promotion).get(context.user_data['promotion_id'])
                context.user_data['found_suffix'] = f'. Акция: <b>{promotion.name}</b>'
                services = [service.to_dict() for service in session.query(Service).all()
                            if service in promotion.services]
            elif context.user_data.get('specialist_id') and _filter:
                spec = session.query(Specialist).get(context.user_data['specialist_id'])
                context.user_data['found_suffix'] = f'. Специалист: <b>{spec.speciality} {spec.full_name}</b>'
                services = [service.to_dict() for service in session.query(Service).all()
                            if spec in service.specialists]
            else:
                services = [service.to_dict() for service in session.query(Service).all()]
        if not context.user_data.get('service_pagination'):
            context.user_data['service_pagination'] = 1
        context.user_data['service_pages_count'] = build_pagination(
            context, services, PAGINATION_STEP, context.user_data['service_pagination'],
            ('услуга', 'услуги', 'услуг'), 'Специалисты',
            context.user_data.get('services.is_sub_already', True),
            found_phrases=['Найдена', 'Найдено', 'Найдено'])
        return (f'{context.user_data["last_block"]}.services.show_all'
                if 'services' not in context.user_data['last_block']
                else f'{context.user_data["last_block"]}.show_all')

    @staticmethod
    def set_next_page(_, context):
        context.user_data['service_pagination'] += 1
        return ServiceViewPublic.show_all(
            _, context, is_sub_already=context.user_data.get('services.is_sub_already', False))

    @staticmethod
    def set_previous_page(_, context):
        context.user_data['service_pagination'] -= 1
        return ServiceViewPublic.show_all(_, context)

    @staticmethod
    def set_page(update, context):
        n = int(update.message.text)
        if not (1 <= n <= context.user_data['service_pages_count']):
            update.message.reply_text('Введён неверный номер страницы')
        else:
            context.user_data['service_pagination'] = n
        return ServiceViewPublic.show_all(
            update, context, is_sub_already=context.user_data.get('services.is_sub_already', False))

    @staticmethod
    def register(update, context: CallbackContext):
        if 'services' not in context.user_data['last_block']:
            context.user_data['last_block'] = f'{context.user_data["last_block"]}.services'
        return Register.register_name(update, context)

    @staticmethod
    @delete_last_message
    def show_specialists(_, context: CallbackContext):
        context.user_data['service_id'] = int(context.match.string)
        if 'services' not in context.user_data['last_block']:
            context.user_data['last_block'] = f'{context.user_data["last_block"]}.services'
        context.user_data['specialists.is_sub_already'] = True
        return SpecialistViewPublic.show_all(_, context, is_sub_already=True)


class PromotionViewPublic:
    @staticmethod
    @delete_last_message
    def show_all(_, context: CallbackContext, is_sub_already: bool = False, _filter: bool = True):
        if ('promotions' in context.user_data.get('last_block', '')
                and not context.user_data.get('last_block', '').endswith('promotions')):
            context.user_data['last_block'] = f'{context.user_data["last_block"].split(".")[0]}.promotions'
        if not is_sub_already:
            context.user_data['promotions.is_sub_already'] = False
        if context.user_data.get('promotion_id'):
            context.user_data.pop('promotion_id')
        if not is_sub_already and context.user_data.get('found_suffix'):
            context.user_data.pop('found_suffix')
        with db_session.create_session() as session:
            if context.user_data.get('service_id') and _filter:
                service = session.query(Service).get(context.user_data['service_id'])
                context.user_data['found_suffix'] = f'. Услуга: <b>{service.name}</b>'
                promotions = [promo.to_dict() for promo in session.query(Promotion).all()
                              if service in promo.services]
            else:
                promotions = [promo.to_dict() for promo in session.query(Promotion).all()]
        if not context.user_data.get('promo_pagination'):
            context.user_data['promo_pagination'] = 1
        context.user_data['promo_pages_count'] = build_pagination(
            context, promotions, PAGINATION_STEP, context.user_data['promo_pagination'],
            ('акция', 'акции', 'акций'), 'Услуги',
            context.user_data.get('promotions.is_sub_already', True),
            found_phrases=['Найдена', 'Найдено', 'Найдено'])
        return (f'{context.user_data["last_block"]}.promotions.show_all'
                if 'promotions' not in context.user_data['last_block']
                else f'{context.user_data["last_block"]}.show_all')

    @staticmethod
    def set_next_page(_, context):
        context.user_data['promo_pagination'] += 1
        return PromotionViewPublic.show_all(
            _, context, is_sub_already=context.user_data.get('promotions.is_sub_already', False))

    @staticmethod
    def set_previous_page(_, context):
        context.user_data['promo_pagination'] -= 1
        return PromotionViewPublic.show_all(
            _, context, is_sub_already=context.user_data.get('promotions.is_sub_already', False))

    @staticmethod
    def set_page(update, context):
        n = int(update.message.text)
        if not (1 <= n <= context.user_data['promo_pages_count']):
            update.message.reply_text('Введён неверный номер страницы')
        else:
            context.user_data['promo_pagination'] = n
        return PromotionViewPublic.show_all(update, context)

    @staticmethod
    def register(update, context: CallbackContext):
        if 'promotions' not in context.user_data['last_block']:
            context.user_data['last_block'] = f'{context.user_data["last_block"]}.promotions'
        return Register.register_name(update, context)

    @staticmethod
    @delete_last_message
    def show_services(_, context: CallbackContext):
        context.user_data['promotion_id'] = int(context.match.string)
        if 'promotions' not in context.user_data['last_block']:
            context.user_data['last_block'] = f'{context.user_data["last_block"]}.promotions'
        context.user_data['services.is_sub_already'] = True
        return ServiceViewPublic.show_all(_, context, is_sub_already=True)

from telegram.ext import CallbackContext
from telegram import InlineKeyboardMarkup, InlineKeyboardButton, ParseMode
from telegram.error import BadRequest

from data.db import db_session
from data.db.models.promotion import Promotion
from data.db.models.service import Service
from data.db.models.specialist import Specialist
from data.utils import delete_last_message, build_pagination, process_view, terminate_jobs, get_config
from data.register import Register


class SpecialistViewPublic:
    @staticmethod
    @delete_last_message
    def show_all(_, context: CallbackContext, is_sub_already=False, _filter=True):
        cfg = get_config()
        if not is_sub_already:
            context.user_data['specialists.is_sub_already'] = False
        if ('specialists' in context.user_data.get('last_block', '')
                and not context.user_data.get('last_block', '').endswith('specialists')):
            context.user_data['last_block'] = f'{context.user_data["last_block"].split(".")[0]}.specialists'
        if context.user_data.get('specialist_id'):
            context.user_data.pop('specialist_id')
        if not is_sub_already and context.user_data.get('found_suffix'):
            context.user_data.pop('found_suffix')
        with db_session.create_session() as session:
            if context.user_data.get('service_id') and _filter:
                service = session.query(Service).get(context.user_data['service_id'])
                context.user_data['found_suffix'] = f'. Услуга: <b>{service.name}</b>'
                specialists = [(spec.id, spec.full_name) for spec in session.query(Specialist).all()
                               if service in spec.services]
            else:
                specialists = [(spec.id, spec.full_name) for spec in session.query(Specialist).all()]
        if not context.user_data.get('spec_pagination'):
            context.user_data['spec_pagination'] = 1
        context.user_data['spec_pages_count'] = build_pagination(
            context, specialists, cfg.get("Шаг пагинации", 7), context.user_data['spec_pagination'],
            ('специалист', 'специалиста', 'специалистов'))
        return (f'{context.user_data["last_block"]}.specialists.show_all'
                if 'specialists' not in context.user_data['last_block']
                else f'{context.user_data["last_block"]}.show_all')

    @staticmethod
    @delete_last_message
    def show_card(_, context: CallbackContext):
        if context.match and context.match.string.isdigit():
            context.user_data['specialist_id'] = int(context.match.string)
        with db_session.create_session() as session:
            spec = session.query(Specialist).get(context.user_data['specialist_id'])
            text = '\n'.join([f'<b>{verbose_name}</b>: {getattr(spec, name) if getattr(spec, name) else "Не указано"}' 
                              for name, verbose_name in spec.verbose_names.items()])
            action_text = context.user_data.get('action_text')
            if isinstance(action_text, dict):
                action_text = action_text['active' if spec.id in context.user_data.get('selected_ids', []) else 'inactive']
            elif not action_text:
                action_text = 'Записаться'
            buttons = [[InlineKeyboardButton(action_text, callback_data=spec.id)],
                       [InlineKeyboardButton('Вернуться назад', callback_data='back')]]
            if not context.user_data['specialists.is_sub_already']:
                buttons.insert(0, [InlineKeyboardButton('Услуги', callback_data=f'services {spec.id}')])
            markup = InlineKeyboardMarkup(buttons)
            callback = (f'{context.user_data["last_block"]}.specialists.show_card' 
                        if 'specialists' not in context.user_data['last_block'] 
                        else f'{context.user_data["last_block"]}.show_card')
            if spec.photo:
                try:
                    return (context.bot.send_photo(context.user_data['id'], spec.photo, text,
                                                   reply_markup=markup, parse_mode=ParseMode.HTML), callback)
                except BadRequest:
                    pass
            return (context.bot.send_message(context.user_data['id'], text,
                                             reply_markup=markup, parse_mode=ParseMode.HTML), callback)

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
        if context.match and context.match.string.split()[-1].isdigit():
            context.user_data['specialist_id'] = int(context.match.string.split()[-1])
        if 'specialists' not in context.user_data['last_block']:
            context.user_data['last_block'] = f'{context.user_data["last_block"]}.specialists'
        context.user_data['services.is_sub_already'] = True
        return ServiceViewPublic.show_all(_, context, is_sub_already=True)


class ServiceViewPublic:
    @staticmethod
    @delete_last_message
    def show_all(_, context: CallbackContext, is_sub_already: bool = False, _filter: bool = True):
        cfg = get_config()
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
                services = [(service.id, service.name) for service in session.query(Service).all()
                            if service in promotion.services]
            elif context.user_data.get('specialist_id') and _filter:
                spec = session.query(Specialist).get(context.user_data['specialist_id'])
                context.user_data['found_suffix'] = f'. Специалист: <b>{spec.speciality} {spec.full_name}</b>'
                services = [(service.id, service.name) for service in session.query(Service).all()
                            if spec in service.specialists]
            else:
                services = [(service.id, service.name) for service in session.query(Service).all()]
        if not context.user_data.get('service_pagination'):
            context.user_data['service_pagination'] = 1
        context.user_data['service_pages_count'] = build_pagination(
            context, services, cfg.get('Шаг пагинации', 7), context.user_data['service_pagination'],
            ('услуга', 'услуги', 'услуг'), found_phrases=['Найдена', 'Найдено', 'Найдено'])
        return (f'{context.user_data["last_block"]}.services.show_all'
                if 'services' not in context.user_data['last_block']
                else f'{context.user_data["last_block"]}.show_all')

    @staticmethod
    @delete_last_message
    def show_card(_, context: CallbackContext):
        if context.match and context.match.string.isdigit():
            context.user_data['service_id'] = int(context.match.string)
        with db_session.create_session() as session:
            service = session.query(Service).get(context.user_data['service_id'])
            text = '\n'.join(
                [f'<b>{verbose_name}</b>: {getattr(service, name) if getattr(service, name) else "Не указано"}'
                 for name, verbose_name in service.verbose_names.items()])
            action_text = context.user_data.get('action_text')
            if isinstance(action_text, dict):
                action_text = (action_text['active' if service.id in context.user_data.get('selected_ids', [])
                               else 'inactive'])
            elif not action_text:
                action_text = 'Записаться'
            buttons = [[InlineKeyboardButton(action_text, callback_data=service.id)],
                       [InlineKeyboardButton('Вернуться назад', callback_data='back')]]
            if not context.user_data['services.is_sub_already']:
                buttons.insert(0, [InlineKeyboardButton('Специалисты', callback_data=f'specialists {service.id}')])
            markup = InlineKeyboardMarkup(buttons)
            callback = (f'{context.user_data["last_block"]}.services.show_card'
                        if 'services' not in context.user_data['last_block']
                        else f'{context.user_data["last_block"]}.show_card')
            if service.photo:
                try:
                    return (context.bot.send_photo(context.user_data['id'], service.photo, text,
                            reply_markup=markup, parse_mode=ParseMode.HTML), callback)
                except BadRequest:
                    pass
            return (context.bot.send_message(context.user_data['id'], text,
                    reply_markup=markup, parse_mode=ParseMode.HTML), callback)

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
        if context.match and context.match.string.split()[-1].isdigit():
            context.user_data['service_id'] = int(context.match.string.split()[-1])
        if 'services' not in context.user_data['last_block']:
            context.user_data['last_block'] = f'{context.user_data["last_block"]}.services'
        context.user_data['specialists.is_sub_already'] = True
        return SpecialistViewPublic.show_all(_, context, is_sub_already=True)


class PromotionViewPublic:
    @staticmethod
    @delete_last_message
    def show_all(_, context: CallbackContext, is_sub_already: bool = False, _filter: bool = True):
        cfg = get_config()
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
                promotions = [(promo.id, promo.name) for promo in session.query(Promotion).all()
                              if service in promo.services]
            else:
                promotions = [(promo.id, promo.name) for promo in session.query(Promotion).all()]
        if not context.user_data.get('promo_pagination'):
            context.user_data['promo_pagination'] = 1
        context.user_data['promo_pages_count'] = build_pagination(
            context, promotions, cfg.get('Шаг пагинации', 7), context.user_data['promo_pagination'],
            ('акция', 'акции', 'акций'), found_phrases=['Найдена', 'Найдено', 'Найдено'])
        return (f'{context.user_data["last_block"]}.promotions.show_all'
                if 'promotions' not in context.user_data['last_block']
                else f'{context.user_data["last_block"]}.show_all')

    @staticmethod
    @delete_last_message
    def show_card(_, context: CallbackContext):
        if context.match and context.match.string.isdigit():
            context.user_data['promotion_id'] = int(context.match.string)
        with db_session.create_session() as session:
            promotion = session.query(Promotion).get(context.user_data['promotion_id'])
            text = '\n'.join(
                [f'<b>{verbose_name}</b>: {getattr(promotion, name) if getattr(promotion, name) else "Не указано"}'
                 for name, verbose_name in promotion.verbose_names.items()])
            action_text = context.user_data.get('action_text')
            if isinstance(action_text, dict):
                action_text = action_text[
                    'active' if promotion.id in context.user_data.get('selected_ids', []) else 'inactive']
            elif not action_text:
                action_text = 'Записаться'
            buttons = [[InlineKeyboardButton(action_text, callback_data=promotion.id)],
                       [InlineKeyboardButton('Вернуться назад', callback_data='back')]]
            if not context.user_data['promotions.is_sub_already']:
                buttons.insert(0, [InlineKeyboardButton('Услуги', callback_data=f'services {promotion.id}')])
            markup = InlineKeyboardMarkup(buttons)
            callback = (f'{context.user_data["last_block"]}.promotions.show_card'
                        if 'services' not in context.user_data['last_block']
                        else f'{context.user_data["last_block"]}.show_card')
            if promotion.photo:
                try:
                    return (context.bot.send_photo(context.user_data['id'], promotion.photo, text,
                                                   reply_markup=markup, parse_mode=ParseMode.HTML), callback)
                except BadRequest:
                    pass
            return (context.bot.send_message(context.user_data['id'], text,
                                             reply_markup=markup, parse_mode=ParseMode.HTML), callback)

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
        if context.match and context.match.string.split()[-1].isdigit():
            context.user_data['promotion_id'] = int(context.match.string.split()[-1])
        if 'promotions' not in context.user_data['last_block']:
            context.user_data['last_block'] = f'{context.user_data["last_block"]}.promotions'
        context.user_data['services.is_sub_already'] = True
        return ServiceViewPublic.show_all(_, context, is_sub_already=True)

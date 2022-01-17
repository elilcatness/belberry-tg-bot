from telegram import InlineKeyboardMarkup, InlineKeyboardButton, ParseMode, Update
from telegram.error import BadRequest
from telegram.ext import CallbackContext

from data.db import db_session
from data.db.models.promotion import Promotion
from data.db.models.service import Service
from data.db.models.specialist import Specialist
from data.utils import delete_last_message, upload_img, clear_temp_vars, delete_img
from data.view import SpecialistViewPublic, ServiceViewPublic, PromotionViewPublic


@delete_last_message
def edit_menu(_, context: CallbackContext):
    clear_temp_vars(context)
    if context.user_data.get('specialist_id'):
        context.user_data.pop('specialist_id')
    if context.user_data.get('service_id'):
        context.user_data.pop('service_id')
    if context.user_data.get('promotion_id'):
        context.user_data.pop('promotion_id')
    context.user_data['last_block'] = 'edit'
    markup = InlineKeyboardMarkup([[InlineKeyboardButton('Специалист', callback_data='edit_specialists')],
                                   [InlineKeyboardButton('Услуга', callback_data='edit_services')],
                                   [InlineKeyboardButton('Акция', callback_data='edit_promotions')],
                                   [InlineKeyboardButton('Вернуться назад', callback_data='back')]])
    return (context.bot.send_message(context.user_data['id'], 'Выберите сущность для редактирования',
                                     reply_markup=markup), 'edit_menu')


class SpecialistEdit:
    @staticmethod
    @delete_last_message
    def show_all(_, context: CallbackContext, is_sub_already=True):
        context.user_data['action_text'] = 'Редактировать'
        SpecialistViewPublic.show_all(_, context, is_sub_already=is_sub_already)
        return 'edit.specialists.show_all'

    @staticmethod
    @delete_last_message
    def edit_menu(_, context: CallbackContext):
        if context.match and context.match.string and context.match.string.split()[0].isdigit():
            context.user_data['specialist_id'] = int(context.match.string.split()[0])
        with db_session.create_session() as session:
            spec = session.query(Specialist).get(context.user_data['specialist_id'])
            buttons = []
            for key, val in spec.verbose_names_edit.items():
                buttons.append([InlineKeyboardButton(val, callback_data=key)])
            buttons.append([InlineKeyboardButton('Вернуться назад', callback_data='back')])
            return (context.bot.send_message(
                context.user_data['id'], f'Редактирование\n\n'
                                         f'<b>Специалист:</b>{spec.speciality} {spec.full_name}',
                reply_markup=InlineKeyboardMarkup(buttons), parse_mode=ParseMode.HTML),
                    'edit.specialists.edit_menu')

    @staticmethod
    @delete_last_message
    def ask_new_value(_, context: CallbackContext):
        context.user_data['key_to_change'] = context.match.string
        markup = InlineKeyboardMarkup([[InlineKeyboardButton('Вернуться назад', callback_data='back')]])
        with db_session.create_session() as session:
            spec = session.query(Specialist).get(context.user_data['specialist_id'])
            if context.user_data['key_to_change'] == 'photo' and spec.photo:
                try:
                    return (context.bot.send_photo(
                        context.user_data['id'], spec.photo,
                        f'На что Вы хотите заменить '
                        f'<b>{spec.verbose_names_edit[context.user_data["key_to_change"]]}</b>?\n\n',
                        reply_markup=markup, parse_mode=ParseMode.HTML), 'edit.specialists.ask_new_value')
                except BadRequest:
                    pass
            return context.bot.send_message(
                context.user_data['id'],
                f'На что Вы хотите заменить '
                f'<b>{spec.verbose_names_edit[context.user_data["key_to_change"]]}</b>?\n\n'
                f'<b>Текущее значение: </b> {getattr(spec, context.user_data["key_to_change"])}',
                reply_markup=markup, parse_mode=ParseMode.HTML,
                disable_web_page_preview=True), 'edit.specialists.ask_new_value'


    @staticmethod
    @delete_last_message
    def set_new_value(update: Update, context: CallbackContext):
        key_to_change = context.user_data['key_to_change']
        with db_session.create_session() as session:
            spec = session.query(Specialist).get(context.user_data['specialist_id'])
            if key_to_change == 'full_name':
                full_name = [word.strip().capitalize() for word in update.message.text.strip().split()]
                if session.query(Specialist).filter(Specialist.full_name == full_name).first():
                    context.bot.send_message(
                        context.user_data['id'],
                        f'Специалист по имени <b>{full_name}</b> уже существует!',
                        parse_mode=ParseMode.HTML)
                    return SpecialistEdit.ask_new_value(update, context)
            elif key_to_change == 'speciality':
                spec.speciality = update.message.text.strip().lower()
            elif key_to_change == 'photo':
                prev_photo = spec.photo
                stream = (update.message.photo[-1].get_file().download_as_bytearray() if update.message.photo
                          else update.message.document.get_file().download_as_bytearray())
                try:
                    spec.photo = upload_img(stream)
                except Exception as e:
                    context.bot.send_message(context.user_data['id'],
                                             f'Выпало следующее исключение: {str(e)}')
                    return SpecialistEdit.ask_new_value(update, context)
                if prev_photo:
                    delete_img(prev_photo)
            else:
                setattr(spec, key_to_change, update.message.text.strip())
            session.add(spec)
            session.commit()
            context.bot.send_message(
                context.user_data['id'],
                f'Переменная <b>{spec.verbose_names_edit[context.user_data.pop("key_to_change")]}</b> '
                f'специалиста <b>{spec.speciality} {spec.full_name}</b> '
                f'была успешно обновлена',
                parse_mode=ParseMode.HTML)
            return SpecialistEdit.edit_menu(update, context)

    @staticmethod
    @delete_last_message
    def show_services(_, context: CallbackContext, reset: bool = True):
        context.user_data['last_block'] = 'edit.specialists'
        context.user_data['action_text'] = {'inactive': 'Выбрать', 'active': 'Выбрано'}
        context.user_data['extra_buttons'] = [('Продолжить', 'next')]
        with db_session.create_session() as session:
            spec = session.query(Specialist).get(context.user_data['specialist_id'])
            if reset:
                count = len(spec.services)
                context.user_data['selected_ids'] = [service.id for service in spec.services]
            else:
                count = len(context.user_data['selected_ids'])
            context.user_data['found_prefix'] = (
                f'Выберите услуги для специалиста <b>'
                f'{spec.speciality} {spec.full_name}</b>\n\n'
                f'<b>Выбрано услуг:</b> {count}\n\n')
        return ServiceViewPublic.show_all(_, context, is_sub_already=True, _filter=False)

    @staticmethod
    @delete_last_message
    def handle_service_selection(_, context: CallbackContext):
        service_id = int(context.match.string.split()[0])
        if service_id in context.user_data['selected_ids']:
            idx = context.user_data['selected_ids'].index(service_id)
            end = (context.user_data['selected_ids'][idx + 1:]
                   if idx + 1 < len(context.user_data['selected_ids']) else [])
            context.user_data['selected_ids'] = context.user_data['selected_ids'][:idx] + end
        else:
            context.user_data['selected_ids'].append(service_id)
        return SpecialistEdit.show_services(_, context, reset=False)

    @staticmethod
    @delete_last_message
    def save_services(_, context: CallbackContext):
        with db_session.create_session() as session:
            spec = session.query(Specialist).get(context.user_data['specialist_id'])
            spec.services = [session.query(Service).get(service_id)
                             for service_id in context.user_data['selected_ids']]
            session.add(spec)
            session.commit()
            context.bot.send_message(
                context.user_data['id'],
                f'<b>Услуги</b> специалиста <b>{spec.speciality} {spec.full_name}</b> '
                f'были успешно обновлены', parse_mode=ParseMode.HTML)
            return SpecialistEdit.edit_menu(_, context)


class ServiceEdit:
    @staticmethod
    @delete_last_message
    def show_all(_, context: CallbackContext, is_sub_already=True):
        context.user_data['action_text'] = 'Редактировать'
        ServiceViewPublic.show_all(_, context, is_sub_already=is_sub_already)
        return 'edit.services.show_all'

    @staticmethod
    @delete_last_message
    def edit_menu(_, context: CallbackContext):
        if context.match and context.match.string and context.match.string.split()[0].isdigit():
            context.user_data['service_id'] = int(context.match.string.split()[0])
        with db_session.create_session() as session:
            service = session.query(Service).get(context.user_data['service_id'])
            buttons = []
            for key, val in service.verbose_names_edit.items():
                buttons.append([InlineKeyboardButton(val, callback_data=key)])
            buttons.append([InlineKeyboardButton('Вернуться назад', callback_data='back')])
            return (context.bot.send_message(
                context.user_data['id'], f'Редактирование\n\n'
                                         f'<b>Услуга:</b> {service.name}',
                reply_markup=InlineKeyboardMarkup(buttons), parse_mode=ParseMode.HTML),
                    'edit.services.edit_menu')

    @staticmethod
    @delete_last_message
    def ask_new_value(_, context: CallbackContext):
        context.user_data['key_to_change'] = context.match.string
        markup = InlineKeyboardMarkup([[InlineKeyboardButton('Вернуться назад', callback_data='back')]])
        with db_session.create_session() as session:
            service = session.query(Service).get(context.user_data['service_id'])
            if context.user_data['key_to_change'] == 'photo' and service.photo:
                try:
                    return (context.bot.send_photo(
                        context.user_data['id'], service.photo,
                        f'На что Вы хотите заменить '
                        f'<b>{service.verbose_names_edit[context.user_data["key_to_change"]]}</b>?\n\n',
                        reply_markup=markup, parse_mode=ParseMode.HTML), 'edit.services.ask_new_value')
                except BadRequest:
                    pass
            return context.bot.send_message(
                context.user_data['id'],
                f'На что Вы хотите заменить '
                f'<b>{service.verbose_names_edit[context.user_data["key_to_change"]]}</b>?\n\n'
                f'<b>Текущее значение: </b> {getattr(service, context.user_data["key_to_change"])}',
                reply_markup=markup, parse_mode=ParseMode.HTML,
                disable_web_page_preview=True), 'edit.services.ask_new_value'


    @staticmethod
    @delete_last_message
    def set_new_value(update: Update, context: CallbackContext):
        key_to_change = context.user_data['key_to_change']
        with db_session.create_session() as session:
            service = session.query(Service).get(context.user_data['service_id'])
            if key_to_change == 'name':
                name = update.message.text.strip().capitalize()
                if session.query(Service).filter(Service.name == name).first():
                    context.bot.send_message(
                        context.user_data['id'],
                        f'Услуга под названием <b>{name}</b> уже существует!',
                        parse_mode=ParseMode.HTML)
                    return ServiceEdit.ask_new_value(update, context)
                service.name = name
            elif key_to_change == 'photo':
                prev_photo = service.photo
                stream = (update.message.photo[-1].get_file().download_as_bytearray() if update.message.photo
                          else update.message.document.get_file().download_as_bytearray())
                try:
                    service.photo = upload_img(stream)
                except Exception as e:
                    context.bot.send_message(context.user_data['id'],
                                             f'Выпало следующее исключение: {str(e)}')
                    return ServiceEdit.ask_new_value(update, context)
                if prev_photo:
                    delete_img(prev_photo)
            else:
                setattr(service, key_to_change, update.message.text.strip())
            session.add(service)
            session.commit()
            context.bot.send_message(
                context.user_data['id'],
                f'Переменная <b>{service.verbose_names_edit[context.user_data.pop("key_to_change")]}</b> '
                f'услуги <b>{service.name}</b> была успешно обновлена', parse_mode=ParseMode.HTML)
            return ServiceEdit.edit_menu(update, context)

    @staticmethod
    @delete_last_message
    def show_specialists(_, context: CallbackContext, reset: bool = True):
        context.user_data['last_block'] = 'edit.services'
        context.user_data['action_text'] = {'inactive': 'Выбрать', 'active': 'Выбрано'}
        context.user_data['extra_buttons'] = [('Продолжить', 'next')]
        with db_session.create_session() as session:
            service = session.query(Service).get(context.user_data['service_id'])
            if reset:
                count = len(service.specialists)
                context.user_data['selected_ids'] = [service.id for service in service.specialists]
            else:
                count = len(context.user_data['selected_ids'])
            context.user_data['found_prefix'] = (
                f'Выберите специалистов, предоставляющих услугу <b>{service.name}</b>\n\n'
                f'<b>Выбрано специалистов:</b> {count}\n\n')
        return SpecialistViewPublic.show_all(_, context, is_sub_already=True, _filter=False)

    @staticmethod
    @delete_last_message
    def handle_specialist_selection(_, context: CallbackContext):
        specialist_id = int(context.match.string.split()[0])
        if specialist_id in context.user_data['selected_ids']:
            idx = context.user_data['selected_ids'].index(specialist_id)
            end = (context.user_data['selected_ids'][idx + 1:]
                   if idx + 1 < len(context.user_data['selected_ids']) else [])
            context.user_data['selected_ids'] = context.user_data['selected_ids'][:idx] + end
        else:
            context.user_data['selected_ids'].append(specialist_id)
        return ServiceEdit.show_specialists(_, context, reset=False)

    @staticmethod
    @delete_last_message
    def save_specialists(_, context: CallbackContext):
        with db_session.create_session() as session:
            service = session.query(Service).get(context.user_data['service_id'])
            service.specialists = [session.query(Specialist).get(specialist_id)
                                   for specialist_id in context.user_data['selected_ids']]
            session.add(service)
            session.commit()
            context.bot.send_message(
                context.user_data['id'],
                f'<b>Специалисты</b> услуги <b>{service.name}</b> '
                f'были успешно обновлены', parse_mode=ParseMode.HTML)
            return ServiceEdit.edit_menu(_, context)


class PromotionEdit:
    @staticmethod
    @delete_last_message
    def show_all(_, context: CallbackContext, is_sub_already=True):
        context.user_data['action_text'] = 'Редактировать'
        PromotionViewPublic.show_all(_, context, is_sub_already=is_sub_already)
        return 'edit.promotions.show_all'

    @staticmethod
    @delete_last_message
    def edit_menu(_, context: CallbackContext):
        if context.match and context.match.string and context.match.string.split()[0].isdigit():
            context.user_data['promotion_id'] = int(context.match.string.split()[0])
        with db_session.create_session() as session:
            promotion = session.query(Promotion).get(context.user_data['promotion_id'])
            buttons = []
            for key, val in promotion.verbose_names_edit.items():
                buttons.append([InlineKeyboardButton(val, callback_data=key)])
            buttons.append([InlineKeyboardButton('Вернуться назад', callback_data='back')])
            return (context.bot.send_message(
                context.user_data['id'], f'Редактирование\n\n'
                                         f'<b>Акция:</b> {promotion.name}',
                reply_markup=InlineKeyboardMarkup(buttons), parse_mode=ParseMode.HTML),
                    'edit.promotions.edit_menu')

    @staticmethod
    @delete_last_message
    def ask_new_value(_, context: CallbackContext):
        context.user_data['key_to_change'] = context.match.string
        markup = InlineKeyboardMarkup([[InlineKeyboardButton('Вернуться назад', callback_data='back')]])
        with db_session.create_session() as session:
            promotion = session.query(Promotion).get(context.user_data['promotion_id'])
            if context.user_data['key_to_change'] == 'photo' and promotion.photo:
                try:
                    return (context.bot.send_photo(
                        context.user_data['id'], promotion.photo,
                        f'На что Вы хотите заменить '
                        f'<b>{promotion.verbose_names_edit[context.user_data["key_to_change"]]}</b>?\n\n',
                        reply_markup=markup, parse_mode=ParseMode.HTML), 'edit.promotions.ask_new_value')
                except BadRequest:
                    pass
            return context.bot.send_message(
                context.user_data['id'],
                f'На что Вы хотите заменить '
                f'<b>{promotion.verbose_names_edit[context.user_data["key_to_change"]]}</b>?\n\n'
                f'<b>Текущее значение: </b> {getattr(promotion, context.user_data["key_to_change"])}',
                reply_markup=markup, parse_mode=ParseMode.HTML,
                disable_web_page_preview=True), 'edit.promotions.ask_new_value'


    @staticmethod
    @delete_last_message
    def set_new_value(update: Update, context: CallbackContext):
        key_to_change = context.user_data['key_to_change']
        with db_session.create_session() as session:
            promotion = session.query(Promotion).get(context.user_data['promotion_id'])
            if key_to_change == 'name':
                name = update.message.text.strip().capitalize()
                if session.query(Promotion).filter(Promotion.name == name).first():
                    context.bot.send_message(
                        context.user_data['id'],
                        f'Акция под названием <b>{name}</b> уже существует!',
                        parse_mode=ParseMode.HTML)
                    return PromotionEdit.ask_new_value(update, context)
                promotion.name = name
            elif key_to_change == 'photo':
                prev_photo = promotion.photo
                stream = (update.message.photo[-1].get_file().download_as_bytearray() if update.message.photo
                          else update.message.document.get_file().download_as_bytearray())
                try:
                    promotion.photo = upload_img(stream)
                except Exception as e:
                    context.bot.send_message(context.user_data['id'],
                                             f'Выпало следующее исключение: {str(e)}')
                    return PromotionEdit.ask_new_value(update, context)
                if prev_photo:
                    delete_img(prev_photo)
            else:
                setattr(promotion, key_to_change, update.message.text.strip())
            session.add(promotion)
            session.commit()
            context.bot.send_message(
                context.user_data['id'],
                f'Переменная <b>{promotion.verbose_names_edit[context.user_data.pop("key_to_change")]}</b> '
                f'акции <b>{promotion.name}</b> была успешно обновлена', parse_mode=ParseMode.HTML)
            return PromotionEdit.edit_menu(update, context)

    @staticmethod
    @delete_last_message
    def show_services(_, context: CallbackContext, reset: bool = True):
        context.user_data['last_block'] = 'edit.promotions'
        context.user_data['action_text'] = {'inactive': 'Выбрать', 'active': 'Выбрано'}
        context.user_data['extra_buttons'] = [('Продолжить', 'next')]
        with db_session.create_session() as session:
            promotion = session.query(Promotion).get(context.user_data['promotion_id'])
            if reset:
                count = len(promotion.services)
                context.user_data['selected_ids'] = [service.id for service in promotion.services]
            else:
                count = len(context.user_data['selected_ids'])
            context.user_data['found_prefix'] = (
                f'Выберите услуги, входящие в акцию <b>{promotion.name}</b>\n\n'
                f'<b>Выбрано услуг:</b> {count}\n\n')
        return ServiceViewPublic.show_all(_, context, is_sub_already=True, _filter=False)

    @staticmethod
    @delete_last_message
    def handle_specialist_selection(_, context: CallbackContext):
        service_id = int(context.match.string.split()[0])
        if service_id in context.user_data['selected_ids']:
            idx = context.user_data['selected_ids'].index(service_id)
            end = (context.user_data['selected_ids'][idx + 1:]
                   if idx + 1 < len(context.user_data['selected_ids']) else [])
            context.user_data['selected_ids'] = context.user_data['selected_ids'][:idx] + end
        else:
            context.user_data['selected_ids'].append(service_id)
        return PromotionEdit.show_services(_, context, reset=False)

    @staticmethod
    @delete_last_message
    def save_services(_, context: CallbackContext):
        with db_session.create_session() as session:
            promotion = session.query(Promotion).get(context.user_data['promotion_id'])
            promotion.services = [session.query(Service).get(service_id)
                                  for service_id in context.user_data['selected_ids']]
            session.add(promotion)
            session.commit()
            context.bot.send_message(
                context.user_data['id'],
                f'<b>Услуги</b> акции <b>{promotion.name}</b> '
                f'были успешно обновлены', parse_mode=ParseMode.HTML)
            return PromotionEdit.edit_menu(_, context)

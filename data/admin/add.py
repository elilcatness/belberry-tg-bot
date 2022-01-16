from telegram import InlineKeyboardMarkup, InlineKeyboardButton, Update, ParseMode
from telegram.ext import CallbackContext

from data.constants import IMG_FILE_SIZE_LIMIT
from data.db import db_session
from data.db.models.service import Service
from data.db.models.specialist import Specialist
from data.general import start
from data.utils import delete_last_message, upload_img, process_view, terminate_jobs
from data.view import ServiceViewPublic, SpecialistViewPublic


@delete_last_message
def add_menu(_, context: CallbackContext):
    context.user_data['last_block'] = 'add'
    markup = InlineKeyboardMarkup([[InlineKeyboardButton('Специалист', callback_data='add_specialists')],
                                   [InlineKeyboardButton('Услуга', callback_data='add_services')],
                                   [InlineKeyboardButton('Вернуться назад', callback_data='back')]])
    return (context.bot.send_message(context.user_data['id'], 'Выберите сущность для добавления',
                                     reply_markup=markup), 'add_menu')


class SpecialistAddition:
    @staticmethod
    @delete_last_message
    def ask_full_name(_, context: CallbackContext):
        context.user_data['specialist_addition'] = dict()
        markup = InlineKeyboardMarkup([[InlineKeyboardButton('Вернуться назад', callback_data='back')]])
        return (context.bot.send_message(context.user_data['id'], 'Введите ФИО специалиста', reply_markup=markup),
                'SpecialistAddition.ask_full_name')

    @staticmethod
    @delete_last_message
    def ask_speciality(update: Update, context: CallbackContext):
        if update.message and update.message.text:
            context.user_data['specialist_addition']['full_name'] = ' '.join([
                word.capitalize() for word in update.message.text.strip().split()])
        with db_session.create_session() as session:
            if session.query(Specialist).filter(
                    Specialist.full_name == context.user_data['specialist_addition']['full_name']).first():
                context.bot.send_message(
                    context.user_data['id'],
                    f'Специалист по имени <b>{context.user_data["specialist_addition"]["full_name"]}</b> '
                    'уже есть в базе!',
                    parse_mode=ParseMode.HTML)
                return SpecialistAddition.ask_full_name(update, context)
        context.user_data['specialist_addition']['speciality'] = None
        markup = InlineKeyboardMarkup(
            [[InlineKeyboardButton('Вернуться назад', callback_data='back')]])
        return (context.bot.send_message(context.user_data['id'], 'Введите специальность',
                                         reply_markup=markup),
                'SpecialistAddition.ask_speciality')

    @staticmethod
    @delete_last_message
    def ask_description(update: Update, context: CallbackContext):
        if update.message and update.message.text:
            context.user_data['specialist_addition']['speciality'] = update.message.text.strip().lower()
        markup = InlineKeyboardMarkup(
            [[InlineKeyboardButton('Пропустить поле «Описание»', callback_data='skip_description')],
             [InlineKeyboardButton('Вернуться назад', callback_data='back')]])
        return (context.bot.send_message(context.user_data['id'], 'Введите описание специалиста',
                                         reply_markup=markup),
                'SpecialistAddition.ask_description')

    @staticmethod
    @delete_last_message
    def ask_services(update: Update, context: CallbackContext):
        if update.message and update.message.text:
            context.user_data['specialist_addition']['description'] = update.message.text.strip()
        context.user_data['selected_ids'] = []
        context.user_data['last_block'] = 'SpecialistAddition'
        context.user_data['action_btn_text'] = {'inactive': 'Выбрать', 'active': 'Выбрано'}
        return ServiceViewPublic.show_all(
            update, context, is_sub_already=True,
            prefix=(f'Выберите услугу для специалиста <b>'
                    f'{context.user_data["specialist_addition"]["speciality"]} '
                    f'{context.user_data["specialist_addition"]["full_name"]}</b>\n\n'
                    f'<b>Выбрано услуг:</b> {len(context.user_data["selected_ids"])}\n\n'),
            extra_buttons=[[InlineKeyboardButton('Продолжить', callback_data='next')]])

    @staticmethod
    def handle_service_selection(_, context: CallbackContext):
        service_id = int(context.match.string.split()[0])
        if service_id in context.user_data['selected_ids']:
            idx = context.user_data['selected_ids'].index(service_id)
            end = (context.user_data['selected_ids'][idx + 1:]
                   if idx + 1 < len(context.user_data['selected_ids']) else [])
            context.user_data['selected_ids'] = context.user_data['selected_ids'][:idx] + end
        else:
            context.user_data['selected_ids'].append(service_id)
        return ServiceViewPublic.show_all(
            _, context, is_sub_already=True,
            prefix=(f'Выберите услугу для специалиста <b>'
                    f'{context.user_data["specialist_addition"]["speciality"]} '
                    f'{context.user_data["specialist_addition"]["full_name"]}</b>\n\n'
                    f'<b>Выбрано услуг:</b> {len(context.user_data["selected_ids"])}\n\n'),
            extra_buttons=[[InlineKeyboardButton('Продолжить', callback_data='next')]])

    @staticmethod
    @delete_last_message
    def ask_photo(_, context: CallbackContext):
        markup = InlineKeyboardMarkup(
            [[InlineKeyboardButton('Пропустить поле «Фото»', callback_data='skip_photo')],
             [InlineKeyboardButton('Вернуться назад', callback_data='back')]])
        return (context.bot.send_message(context.user_data['id'], 'Отправьте фото специалиста',
                                         reply_markup=markup),
                'SpecialistAddition.ask_photo')

    @staticmethod
    @delete_last_message
    def finish(update: Update, context: CallbackContext):
        if update.message:
            stream = (update.message.photo[-1].get_file().download_as_bytearray() if update.message.photo
                      else update.message.document.get_file().download_as_bytearray())
            try:
                context.user_data['specialist_addition']['photo'] = upload_img(stream)
            except Exception as e:
                context.bot.send_message(context.user_data['id'], f'Выпало следующее исключение: {str(e)}')
                return SpecialistAddition.ask_photo(update, context)
        with db_session.create_session() as session:
            full_name = context.user_data['specialist_addition']['full_name']
            spec = Specialist(**context.user_data.pop('specialist_addition'))
            session.add(spec)
            session.commit()
            for service_id in context.user_data['selected_ids']:
                service = session.query(Service).get(service_id)
                spec.services.append(service)
                session.add(spec)
                session.commit()
        if context.user_data.get('selected_ids'):
            context.user_data.pop('selected_ids')
        if context.user_data.get('action_btn_text'):
            context.user_data.pop('action_btn_text')
        context.bot.send_message(context.user_data['id'],
                                 f'Специалист <b>{full_name}</b> был успешно добавлен',
                                 parse_mode=ParseMode.HTML)
        return start(update, context)


class ServiceAddition:
    @staticmethod
    @delete_last_message
    def ask_name(_, context: CallbackContext):
        context.user_data['service_addition'] = dict()
        markup = InlineKeyboardMarkup([[InlineKeyboardButton('Вернуться назад', callback_data='back')]])
        return (context.bot.send_message(context.user_data['id'], 'Введите название услуги',
                                         reply_markup=markup),
                'ServiceAddition.ask_name')

    @staticmethod
    @delete_last_message
    def ask_description(update: Update, context: CallbackContext):
        if update.message and update.message.text:
            context.user_data['service_addition']['name'] = update.message.text.strip()
        with db_session.create_session() as session:
            for service in session.query(Service).all():
                if service.name.lower() == context.user_data['service_addition']['name'].lower():
                    context.bot.send_message(
                        context.user_data['id'],
                        f'Услуга <b>{context.user_data["service_addition"]["name"]}</b> уже существует!',
                        parse_mode=ParseMode.HTML)
                    return ServiceAddition.ask_name(update, context)
        markup = InlineKeyboardMarkup(
            [[InlineKeyboardButton('Пропустить поле «Описание»', callback_data='skip_description')],
             [InlineKeyboardButton('Вернуться назад', callback_data='back')]])
        return (context.bot.send_message(context.user_data['id'], 'Введите описание услуги',
                                         reply_markup=markup),
                'ServiceAddition.ask_description')

    @staticmethod
    @delete_last_message
    def ask_specialists(update: Update, context: CallbackContext):
        if update.message and update.message.text:
            context.user_data['service_addition']['description'] = update.message.text.strip()
        context.user_data['selected_ids'] = []
        context.user_data['last_block'] = 'ServiceAddition'
        context.user_data['action_btn_text'] = {'inactive': 'Выбрать', 'active': 'Выбрано'}
        return SpecialistViewPublic.show_all(
            update, context, is_sub_already=True,
            prefix=(f'Выберите специалистов, предоставляющих услугу <b>'
                    f'{context.user_data["service_addition"]["name"]}</b>\n\n'
                    f'<b>Выбрано специалистов:</b> {len(context.user_data["selected_ids"])}\n\n'),
            extra_buttons=[[InlineKeyboardButton('Продолжить', callback_data='next')],
                           [InlineKeyboardButton('Пропустить поле «Специалисты»',
                                                 callback_data='skip_specialists')]])

    @staticmethod
    def handle_specialist_selection(_, context: CallbackContext):
        spec_id = int(context.match.string.split()[0])
        if spec_id in context.user_data['selected_ids']:
            idx = context.user_data['selected_ids'].index(spec_id)
            end = (context.user_data['selected_ids'][idx + 1:]
                   if idx + 1 < len(context.user_data['selected_ids']) else [])
            context.user_data['selected_ids'] = context.user_data['selected_ids'][:idx] + end
        else:
            context.user_data['selected_ids'].append(spec_id)
        return SpecialistViewPublic.show_all(
            _, context, is_sub_already=True,
            prefix=(f'Выберите специалистов, предоставляющих услугу <b>'
                    f'{context.user_data["service_addition"]["name"]}</b>\n\n'
                    f'<b>Выбрано специалистов:</b> {len(context.user_data["selected_ids"])}\n\n'),
            extra_buttons=[[InlineKeyboardButton('Продолжить', callback_data='next')],
                           [InlineKeyboardButton('Пропустить поле «Специалисты»',
                                                 callback_data='skip_specialists')]])

    @staticmethod
    @delete_last_message
    def ask_photo(_, context: CallbackContext):
        if context.match and context.match.string and context.match.string == 'skip_descriptions':
            context.user_data['selected_ids'] = []
        markup = InlineKeyboardMarkup(
            [[InlineKeyboardButton('Пропустить поле «Фотография»', callback_data='skip_photo')],
             [InlineKeyboardButton('Вернуться назад', callback_data='back')]])
        return (context.bot.send_message(context.user_data['id'], 'Отправьте фото услуги',
                                         reply_markup=markup),
                'ServiceAddition.ask_photo')

    @staticmethod
    @delete_last_message
    def finish(update: Update, context: CallbackContext):
        if update.message:
            job_name = f'process {context.user_data["id"]}'
            context.user_data['process.msg_text'] = 'Подождите. Фотография обрабатывается'
            context.job_queue.run_repeating(process_view, 1, 0,
                                            context=context, name=job_name)
            stream = (update.message.photo[-1].get_file().download_as_bytearray() if update.message.photo
                      else update.message.document.get_file().download_as_bytearray())
            try:
                url = upload_img(stream)
                if not url:
                    context.bot.send_message(
                        context.user_data['id'],
                        'Не удалось загрузить изображение. '
                        f'Возможно, был превышен лимит размера фотографии ({IMG_FILE_SIZE_LIMIT} МБ')
                    return ServiceAddition.ask_photo(update, context)
                context.user_data['service_addition']['photo'] = url
            except Exception as e:
                context.bot.send_message(context.user_data['id'], f'Выпало следующее исключение: {str(e)}')
                return ServiceAddition.ask_photo(update, context)
            finally:
                terminate_jobs(context, job_name)
        with db_session.create_session() as session:
            name = context.user_data['service_addition']['name']
            service = Service(**context.user_data.pop('service_addition'))
            session.add(service)
            session.commit()
            for spec_id in context.user_data['selected_ids']:
                spec = session.query(Specialist).get(spec_id)
                service.specialists.append(spec)
                session.add(service)
                session.commit()
        context.user_data['selected_ids'] = []
        context.user_data['action_btn_text'] = None
        context.bot.send_message(context.user_data['id'],
                                 f'Услуга <b>{name}</b> была успешно добавлена',
                                 parse_mode=ParseMode.HTML)
        return add_menu(update, context)

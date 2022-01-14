from telegram import InlineKeyboardMarkup, InlineKeyboardButton, Update, ParseMode
from telegram.ext import CallbackContext

from data.db import db_session
from data.db.models.specialist import Specialist
from data.general import start
from data.utils import delete_last_message, upload_img


@delete_last_message
def add_menu(_, context: CallbackContext):
    markup = InlineKeyboardMarkup([[InlineKeyboardButton('Специалисты', callback_data='add_specialists')],
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
        if update.message:
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
        if update.message:
            context.user_data['specialist_addition']['speciality'] = update.message.text.strip().capitalize()
        markup = InlineKeyboardMarkup(
            [[InlineKeyboardButton('Вернуться назад', callback_data='back')],
             [InlineKeyboardButton('Пропустить поле «Описание»', callback_data='skip_description')]])
        return (context.bot.send_message(context.user_data['id'], 'Введите описание специалиста',
                                         reply_markup=markup),
                'SpecialistAddition.ask_description')

    @staticmethod
    @delete_last_message
    def ask_photo(update: Update, context: CallbackContext):
        if update.message:
            context.user_data['specialist_addition']['description'] = update.message.text.strip()
        markup = InlineKeyboardMarkup(
            [[InlineKeyboardButton('Вернуться назад', callback_data='back')],
             [InlineKeyboardButton('Пропустить поле «Фото»', callback_data='skip_photo')]])
        return (context.bot.send_message(context.user_data['id'], 'Отправьте фото специалиста',
                                         reply_markup=markup),
                'SpecialistAddition.ask_photo')

    @staticmethod
    @delete_last_message
    def finish(update: Update, context: CallbackContext):
        if update.message and update.message.photo:
            stream = update.message.photo[-1].get_file().download_as_bytearray()
            try:
                url = upload_img(stream)
            except Exception as e:
                return context.bot.send_message(f'Выпало следующее исключение: {str(e)}')
            context.user_data['specialist_addition']['photo'] = url
        with db_session.create_session() as session:
            full_name = context.user_data['specialist_addition']['full_name']
            session.add(Specialist(**context.user_data.pop('specialist_addition')))
            session.commit()
        context.bot.send_message(context.user_data['id'],
                                 f'Специалист <b>{full_name}</b> был успешно добавлен',
                                 parse_mode=ParseMode.HTML)
        return start(update, context)

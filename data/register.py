from telegram import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove

from data.db import db_session
from data.general import start
from data.help import help_menu
from data.mail_sender import send_mail
from data.utils import get_config, delete_last_message

from data.db.models.specialist import Specialist
from data.db.models.service import Service
from data.db.models.promotion import Promotion


class Register:
    return_functions = {
        'info.specialists': ('from data.view import SpecialistViewPublic',
                             'SpecialistViewPublic.show_all',
                             'info'),
        'info.specialists.services': ('from data.view import SpecialistViewPublic',
                                      'SpecialistViewPublic.show_all',
                                      'info'),
        'info.services': ('from data.view import ServiceViewPublic',
                          'ServiceViewPublic.show_all',
                          'info'),
        'info.services.specialists': ('from data.view import ServiceViewPublic',
                                      'ServiceViewPublic.show_all',
                                      'info'),
        'help': ('from data.help import help_menu', 'help_menu', 'help'),
        'help.promotions': ('from data.view import PromotionViewPublic',
                            'PromotionViewPublic.show_all',
                            'help'),
        'help.promotions.services': ('from data.view import PromotionViewPublic',
                                     'PromotionViewPublic.show_all',
                                     'help'),
        'help.promotions.services.specialists': ('from data.view import SpecialistViewPublic',
                                                 'PromotionViewPublic.show_all',
                                                 'help'),
        'help.specialists': ('from data.view import SpecialistViewPublic',
                             'SpecialistViewPublic.show_all',
                             'help'),
        'help.specialists.services': ('from data.view import SpecialistViewPublic',
                                      'SpecialistViewPublic.show_all',
                                      'help'),
        'help.services': ('from data.view import ServiceViewPublic',
                          'ServiceViewPublic.show_all',
                          'help'),
        'help.services.specialists': ('from data.view import ServiceViewPublic',
                                      'ServiceViewPublic.show_all',
                                      'help'),
    }

    @staticmethod
    @delete_last_message
    def register_name(_, context):
        if not get_config().get('email'):
            context.bot.send_message(
                context.user_data['id'],
                'Запись в данный момент недоступна из-за технических неполадок',
                reply_markup=ReplyKeyboardRemove())
            return help_menu(_, context)
        last_block = context.user_data.get('last_block')
        if last_block:
            callback = f'{last_block}.register_name'
            context.user_data['consult_return_fn'] = Register.return_functions[last_block]
        else:
            callback = 'register_name'
        if 'specialists' in last_block:
            _type = 'Specialist'
            entity_id = int(context.match.string.split()[0])
        elif 'services' in last_block:
            _type = 'Service'
            entity_id = int(context.match.string.split()[0])
        elif 'promotions' in last_block:
            _type = 'Promotion'
            entity_id = int(context.match.string.split()[0])
        else:
            _type, entity_id = None, None
        context.user_data['register'] = {'_type': _type, 'entity_id': entity_id}
        markup = ReplyKeyboardMarkup([[KeyboardButton('Вернуться назад')]], resize_keyboard=True,
                                     one_time_keyboard=True)
        return context.bot.send_message(context.user_data['id'], 'Введите своё имя',
                                        reply_markup=markup), callback

    @staticmethod
    @delete_last_message
    def register_phone(update, context):
        context.user_data['register']['Имя'] = update.message.text
        markup = ReplyKeyboardMarkup([[KeyboardButton('Взять из Telegram', request_contact=True)],
                                      [KeyboardButton('Вернуться назад')]],
                                     resize_keyboard=True, one_time_keyboard=True)
        return (context.bot.send_message(
            context.user_data['id'], 'Укажите свой номер телефона', reply_markup=markup),
                f'{context.user_data["last_block"]}.register_phone')

    @staticmethod
    @delete_last_message
    def finish(update, context):
        context.user_data['register']['Номер телефона'] = (
            update.message.contact.phone_number
            if getattr(update.message, 'contact') and getattr(update.message.contact, 'phone_number')
            else update.message.text)
        markup = ReplyKeyboardRemove()
        _type = context.user_data['register'].pop('_type')
        entity_id = context.user_data['register'].pop('entity_id')
        if _type:
            with db_session.create_session() as session:
                entity = session.query(eval(_type)).get(entity_id)
                if _type == 'Specialist':
                    prefix = f'к специалисту <b>{entity.speciality} {entity.full_name}</b> '
                elif _type == 'Service':
                    prefix = f'на услугу <b>{entity.name}</b> '
                elif _type == 'Promotion':
                    prefix = f'на акцию <b>{entity.name}</b>'
        else:
            prefix = ''
        if not send_mail(get_config().get('email', {}).get('val'), 'Заявка на запись',
                         f'Поступила заявка на запись {prefix}со следующими данными:<br><br> '
                         '%s' % ('<br>'.join([f'<b>{key}</b>: {val}'
                                              for key, val in context.user_data['register'].items()]))
                         + f'<div align="right"><i>Уведомление было отправлено автоматически от Telegram бота '
                           f'https://t.me/{context.bot.username}</i></div>'):
            update.message.reply_text('Произошла ошибка при создании заявки', reply_markup=markup)
        else:
            update.message.reply_text('Ваша заявка была успешно отправлена. Ожидайте звонка',
                                      reply_markup=markup)
        if context.user_data.get('consult_return_fn'):
            import_statement, func, last_block = context.user_data.pop('consult_return_fn')
            exec(import_statement)
            context.user_data['last_block'] = last_block
            return eval(f'{func}(update, context)')
        return start(update, context)

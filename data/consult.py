from telegram import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove

from data.general import start
from data.mail_sender import send_mail
from data.utils import delete_last_message, get_config

from data.info import about  # Для автоматических вызовов


class Consult:
    return_functions = {
        'about': 'about'
    }

    @staticmethod
    @delete_last_message
    def ask_phone(_, context):
        markup = ReplyKeyboardMarkup([[KeyboardButton('Взять из Telegram', request_contact=True)],
                                      [KeyboardButton('Вернуться назад')]],
                                     resize_keyboard=True, one_time_keyboard=True)
        last_block = context.user_data.get('last_block')
        if last_block:
            callback = f'{last_block}.consult'
            context.user_data['consult_return_fn'] = Consult.return_functions[last_block]
        else:
            callback = 'consult'
        return context.bot.send_message(
            context.user_data['id'], 'Я так рад, что Вы уже были у нас!\n\n'
                                     'Оставьте Ваш номер телефона, и мы перезвоним',
            reply_markup=markup), callback

    @staticmethod
    @delete_last_message
    def finish(update, context):
        cfg = get_config()
        phone_number = (update.message.contact.phone_number
                        if getattr(update.message, 'contact')
                        and getattr(update.message.contact, 'phone_number') else update.message.text)
        markup = ReplyKeyboardRemove()
        email = cfg.get('email', {}).get('val', [])
        if isinstance(email, list) and len(email) > 1:
            email = email[0]
        if not email or not send_mail(
                email, 'Заявка на консультацию',
                f'Заявка на консультацию поступила с указанием следующего номера: {phone_number}\n\n'
                f'<br><div align="right"><i>Уведомление было отправлено автоматически от Telegram бота '
                f'https://t.me/{context.bot.username}</i></div>'):
            update.message.reply_text('Произошла ошибка при создании заявки', reply_markup=markup)
        else:
            update.message.reply_text('Спасибо за заявку. Мы как можно скорее с Вами свяжемся',
                                      reply_markup=markup)
        if context.user_data.get('consult_return_fn'):
            return eval(f'{context.user_data.pop("consult_return_fn")}(update, context)')
        return start(update, context)
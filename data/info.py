from telegram import InlineKeyboardMarkup, InlineKeyboardButton, ParseMode
from telegram.ext import CallbackContext

from data.utils import get_config, delete_last_message


@delete_last_message
def info_menu(_, context: CallbackContext):
    cfg = get_config()
    markup = InlineKeyboardMarkup(
        [[InlineKeyboardButton('Услуги', callback_data='services')],
         [InlineKeyboardButton('Специалисты', callback_data='specialists')],
         [InlineKeyboardButton('О нас', callback_data='about')],
         [InlineKeyboardButton('Наш адрес', callback_data='address')],
         [InlineKeyboardButton('Наши соц.сети', callback_data='socials')],
         [InlineKeyboardButton('Перейти на сайт', url=cfg.get('URL клиники', 'https://belberry.net'))],
         [InlineKeyboardButton('Рейтинг клиники и отзывы', url=cfg.get('URL для отзыва', 'https://belberry.net'))],
         [InlineKeyboardButton('Вернуться назад', callback_data='back')]]
    )
    return (context.bot.send_message(context.user_data['id'], 'Выберите опцию', reply_markup=markup),
            'info_menu')


@delete_last_message
def about(_, context):
    cfg = get_config()
    markup = InlineKeyboardMarkup([[InlineKeyboardButton('Вернуться назад', callback_data='back')]])
    phone_key = 'Наш телефон'
    phone = cfg.get('Номер телефона клиники', 'Не указан')
    if len(phone.split(';')) > 1:
        phone = '\n' + '\n'.join([f'• {ph}' for ph in phone.split(';')])
        phone_key = 'Наши телефоны'
    mail = cfg.get('email', 'Не указан')
    if len(mail.split(';')) > 1:
        mail = '\n' + '\n'.join([f'• {m}' for m in mail.split(';')])
    return ((context.user_data['id'], f'{cfg.get("Описание клиники", "На данный момент описания нет")}\n\n'
                                      f'<b>{phone_key}:</b> {phone}\n\n'
                                      f'<b>E-Mail</b>: {mail}'),
            {'reply_markup': markup, 'parse_mode': ParseMode.HTML}, 'about_menu')


@delete_last_message
def show_address(_, context: CallbackContext):
    cfg = get_config()
    markup = InlineKeyboardMarkup(
        [[InlineKeyboardButton('Проложить маршрут', callback_data='route')],
         [InlineKeyboardButton('Вернуться назад', callback_data='back')]])
    text = f'<b>Наш адрес:</b> {cfg.get("Адрес клиники", "Не указан")}'
    if cfg.get('Фото карты'):
        return (context.bot.send_photo(context.user_data['id'], cfg['Фото карты'], text,
                                       reply_markup=markup, parse_mode=ParseMode.HTML),
                'address_menu')
    return context.bot.send_message(context.user_data['id'], text, reply_markup=markup,
                                    parse_mode=ParseMode.HTML), 'address_menu'


@delete_last_message
def choose_route_engine(_, context: CallbackContext):
    cfg = get_config()
    buttons = []
    any_route = False
    if cfg.get('URL маршрута 2ГИС') and cfg['URL маршрута 2ГИС'].startswith('http'):
        any_route = True
        buttons.append([InlineKeyboardButton('2ГИС', url=cfg['URL маршрута 2ГИС'])])
    if cfg.get('URL маршрута Яндекс.Карты') and cfg['URL маршрута Яндекс.Карты'].startswith('http'):
        any_route = True
        buttons.append([InlineKeyboardButton('Яндекс.Карты', url=cfg['URL маршрута Яндекс.Карты'])])
    text = ('Выберите сервис для прокладывания маршрута' if any_route
            else 'Функция прокладывания маршрута недоступна на данный момент')
    buttons.append([InlineKeyboardButton('Вернуться назад', callback_data='back')])
    return context.bot.send_message(context.user_data['id'], text,
                                    reply_markup=InlineKeyboardMarkup(buttons)), 'route_menu'


@delete_last_message
def show_socials(_, context: CallbackContext):
    cfg = get_config()
    markup = InlineKeyboardMarkup([[InlineKeyboardButton('Вернуться назад', callback_data='back')]])
    if cfg.get('Соц.сети'):
        text = ('<b>Наши социальные сети:</b>\n\n' +
                '\n'.join([f'• {s}' for s in cfg['Соц.сети']]))
    else:
        text = 'На данный момент у клиники не указаны никакие социальные сети'
    return context.bot.send_message(
        context.user_data['id'], text, reply_markup=markup, parse_mode=ParseMode.HTML,
        disable_web_page_preview=True), 'socials_menu'
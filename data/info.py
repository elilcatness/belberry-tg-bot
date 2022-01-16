from telegram import InlineKeyboardMarkup, InlineKeyboardButton, ParseMode
from telegram.ext import CallbackContext

from data.utils import get_config, delete_last_message


@delete_last_message
def info_menu(_, context: CallbackContext):
    if context.user_data.get('specialist_id'):
        context.user_data.pop('specialist_id')
    if context.user_data.get('service_id'):
        context.user_data.pop('service_id')
    cfg = get_config()
    context.user_data['last_block'] = 'info'
    markup = InlineKeyboardMarkup(
        [[InlineKeyboardButton('Услуги', callback_data='services')],
         [InlineKeyboardButton('Специалисты', callback_data='specialists')],
         [InlineKeyboardButton('О нас', callback_data='about')],
         [InlineKeyboardButton('Наш адрес', callback_data='address')],
         [InlineKeyboardButton('Наши соц.сети', callback_data='socials')],
         [InlineKeyboardButton('Перейти на сайт',
                               url=cfg.get('URL клиники', {}).get('val', 'https://belberry.net'))],
         [InlineKeyboardButton('Рейтинг клиники и отзывы',
                               url=cfg.get('URL для отзыва', {}).get('val', 'https://belberry.net'))],
         [InlineKeyboardButton('Вернуться назад', callback_data='back')]]
    )
    return (context.bot.send_message(context.user_data['id'], 'Выберите опцию', reply_markup=markup),
            'info_menu')


@delete_last_message
def about(_, context: CallbackContext):
    context.user_data['last_block'] = 'about'
    cfg = get_config()
    markup = InlineKeyboardMarkup(
        [[InlineKeyboardButton('Проконсультироваться по телефону', callback_data='about.consult')],
         [InlineKeyboardButton('Вернуться назад', callback_data='back')]])
    # phones = cfg.get('Номер телефона', {}).get('val', 'Не указан')
    # if isinstance(phones, list) and len(phones) > 1:
    #     phone_key = 'Наши номера телефонов'
    #     phones = '\n' + '\n'.join([f'• {ph}' for ph in phones])
    # else:
    #     phone_key = 'Наш номер телефона'
    # e_mails = cfg.get('email', {}).get('val', 'Не указан')
    # if isinstance(e_mails, list) and len(e_mails) > 1:
    #     e_mail_key = 'Наши E-mail'
    #     e_mails = '\n' + '\n'.join([f'• {e}' for e in e_mails])
    # else:
    #     e_mail_key = 'Наш E-mail'
    return (context.bot.send_message(
        context.user_data['id'],
        cfg.get("Описание клиники", {}).get("val", "На данный момент описание клиники не указано"),
        reply_markup=markup, disable_web_page_preview=True, parse_mode=ParseMode.HTML), 'about_menu')


@delete_last_message
def show_address(_, context: CallbackContext):
    cfg = get_config()
    markup = InlineKeyboardMarkup(
        [[InlineKeyboardButton('Проложить маршрут', callback_data='route')],
         [InlineKeyboardButton('Вернуться назад', callback_data='back')]])
    text = f'<b>Наш адрес:</b> {cfg.get("Адрес клиники", {}).get("val", "Не указан")}'
    if cfg.get('Фото карты', {}).get('val'):
        return (context.bot.send_photo(context.user_data['id'], cfg['Фото карты']['val'], text,
                                       reply_markup=markup, parse_mode=ParseMode.HTML),
                'address_menu')
    return context.bot.send_message(context.user_data['id'], text, reply_markup=markup,
                                    parse_mode=ParseMode.HTML), 'address_menu'


@delete_last_message
def choose_route_engine(_, context: CallbackContext):
    cfg = get_config()
    buttons = []
    any_route = False
    if cfg.get('URL маршрута 2ГИС', {}).get('val') and cfg['URL маршрута 2ГИС']['val'].startswith('http'):
        any_route = True
        buttons.append([InlineKeyboardButton('2ГИС', url=cfg['URL маршрута 2ГИС']['val'])])
    if (cfg.get('URL маршрута Яндекс.Карты', {}).get('val')
            and cfg['URL маршрута Яндекс.Карты']['val'].startswith('http')):
        any_route = True
        buttons.append([InlineKeyboardButton('Яндекс.Карты', url=cfg['URL маршрута Яндекс.Карты']['val'])])
    text = ('Выберите сервис для прокладывания маршрута' if any_route
            else 'Функция прокладывания маршрута недоступна на данный момент')
    buttons.append([InlineKeyboardButton('Вернуться назад', callback_data='back')])
    return context.bot.send_message(context.user_data['id'], text,
                                    reply_markup=InlineKeyboardMarkup(buttons)), 'route_menu'


@delete_last_message
def show_socials(_, context: CallbackContext):
    cfg = get_config()
    markup = InlineKeyboardMarkup([[InlineKeyboardButton('Вернуться назад', callback_data='back')]])
    if cfg.get('Соц.сети', {}).get('val'):
        text = ('<b>Наши социальные сети:</b>\n\n' +
                '\n'.join([f'• {s}' for s in cfg['Соц.сети']['val']]))
    else:
        text = 'На данный момент у клиники не указаны никакие социальные сети'
    return context.bot.send_message(
        context.user_data['id'], text, reply_markup=markup, parse_mode=ParseMode.HTML,
        disable_web_page_preview=True), 'socials_menu'
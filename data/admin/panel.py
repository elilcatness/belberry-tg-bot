import json
import os

from telegram import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton, ParseMode

from data.general import start
from data.utils import delete_last_message, get_config, save_config


@delete_last_message
def show_data(_, context):
    cfg = get_config()
    markup = InlineKeyboardMarkup(
        [[InlineKeyboardButton(text=key, callback_data=key)] for key in cfg.keys()] +
        [[InlineKeyboardButton(text='Вернуться назад', callback_data='menu')]])
    return (context.user_data['id'], 'Выберите переменную'), {'reply_markup': markup}, 'data_requesting'


@delete_last_message
def request_changing_data(_, context):
    context.user_data['key_to_change'] = context.match.string
    current_value = get_config()[context.match.string]
    if isinstance(current_value, list):
        current_value = ';'.join(map(str, current_value))
    markup = InlineKeyboardMarkup(
        [[InlineKeyboardButton(text='Вернуться назад', callback_data='data')]])
    return ((context.user_data['id'], f'На что вы хотите заменить <b>{context.match.string}</b>?\n'
                                      f'\n<b>Текущее значение:</b> {current_value}\n'
                                      'Если это список, то введите элементы через ;'),
            {'reply_markup': markup, 'disable_web_page_preview': True, 'parse_mode': ParseMode.HTML},
            'data')


@delete_last_message
def change_data(update, context):
    if context.user_data.get('message_id'):
        context.bot.deleteMessage(context.user_data['id'], context.user_data.pop('message_id'))
    cfg = get_config()
    key = context.user_data['key_to_change']
    if key == 'admins' and str(update.message.from_user.id) not in update.message.text.split(';'):
        update.message.reply_text('Вы не можете удалить сами себя из admins')
        return show_data(update, context)
    if isinstance(cfg[key], list):
        cfg[key] = [val.strip() for val in update.message.text.split(';')]
    else:
        cfg[key] = update.message.text.strip()
    save_config(cfg)
    update.message.reply_text(f'Переменная <b>{context.user_data["key_to_change"]}</b> была обновлена',
                              parse_mode=ParseMode.HTML)
    return show_data(update, context)


@delete_last_message
def ask_resetting_data(_, context):
    markup = InlineKeyboardMarkup([[InlineKeyboardButton('Да', callback_data='change_yes')],
                                  [InlineKeyboardButton('Нет', callback_data='change_no')]])
    print(markup)
    return ((context.user_data['id'], 'Вы уверены, что хотите сбросить настройки до серверных?'),
            {'reply_markup': markup}), 'data_resetting'


@delete_last_message
def reset_data(update, context):
    if update.message.text == 'Да':
        with open(os.path.join('data', 'config.json'), encoding='utf-8') as f:
            cfg = get_config()
            admins = cfg['admins']
            data = json.loads(f.read())
            data['admins'] = admins
            save_config(data)
            update.message.reply_text('Настройки были успешно сброшены')
    return start(update, context)

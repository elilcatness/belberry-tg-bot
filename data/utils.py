import json
import os
from typing import Union

from cloudinary import uploader
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ParseMode
from telegram.error import BadRequest
from telegram.ext import CallbackContext

from data.db import db_session
from data.db.models.config import Config
from data.db.models.state import State


def delete_last_message(func):
    def wrapper(update, context: CallbackContext, **kwargs):
        if context.user_data.get('message_id'):
            try:
                context.bot.deleteMessage(context.user_data['id'], context.user_data.pop('message_id'))
            except BadRequest:
                pass
        while context.user_data.get('messages_to_delete'):
            try:
                context.bot.deleteMessage(context.user_data['id'],
                                          context.user_data['messages_to_delete'].pop(0))
            except BadRequest:
                pass
        output = func(update, context, **kwargs)
        if isinstance(output, tuple):
            msg, callback = output
            context.user_data['message_id'] = msg.message_id
        else:
            callback = output
        save_state(context.user_data['id'], callback, context.user_data)
        return callback

    return wrapper


def save_state(user_id: int, callback: str, data: dict):
    with db_session.create_session() as session:
        state = session.query(State).get(user_id)
        str_data = json.dumps(data)
        if state:
            state.user_id = user_id
            state.callback = callback
            state.data = str_data
        else:
            state = State(user_id=user_id, callback=callback, data=str_data)
        session.add(state)
        session.commit()


def get_current_state(user_id: int):
    with db_session.create_session() as session:
        return session.query(State).get(user_id)


def get_config():
    with db_session.create_session() as session:
        try:
            cfg = json.loads(session.query(Config).first().text)
        except AttributeError:
            with open(os.path.join('data', 'config.json'), encoding='utf-8') as f:
                data = f.read()
                session.add(Config(text=data))
                session.commit()
                cfg = json.loads(data)
    return cfg


def save_config(cfg):
    with db_session.create_session() as session:
        config = session.query(Config).first()
        if not config:
            session.add(Config(text=json.dumps(cfg)))
        else:
            config.text = json.dumps(cfg)
            session.merge(config)
        session.commit()


def upload_img(img_stream: bytes):
    return uploader.upload_image(img_stream).url


def delete_img(url: str):
    uploader.destroy(url.split('/')[-1].split('.')[0])


def terminate_jobs(context: CallbackContext, name: str):
    for job in context.job_queue.get_jobs_by_name(name):
        job.schedule_removal()
    if 'process' in name:
        msg_id = context.user_data.get('process.msg_id')
        if msg_id:
            try:
                context.bot.delete_message(context.user_data['id'], msg_id)
            except BadRequest:
                pass
        keys = [k for k in context.user_data.keys() if k.startswith('process')]
        for key in keys:
            context.user_data.pop(key)


def process_view(context: CallbackContext):
    user_id = context.job.context.user_data['id']
    msg_id = context.job.context.user_data.get('process.msg_id')
    msg_text = context.job.context.user_data['process.msg_text']
    count = context.job.context.user_data.get('process.count', 0)
    if not msg_id:
        context.job.context.user_data['process.msg_id'] = context.bot.send_message(
            user_id, f'{msg_text}{"." * count}').message_id
    else:
        try:
            context.bot.edit_message_text(f'{msg_text}{"." * count}', user_id, msg_id)
        except BadRequest:
            pass
    context.job.context.user_data['process.count'] = (count + 1) % 4


def make_agree_with_number(n: int, verbose_names: list):
    if str(n)[-1] == '1' and n != 11:
        return verbose_names[0]
    elif str(n)[-1] in ['2', '3', '4'] and str(n) not in ['12', '13', '14']:
        return verbose_names[1]
    return verbose_names[2]


def build_pagination(context: CallbackContext, array: list,
                     pag_step: int, current_page: int, verbose_names: list,
                     found_phrases: list = None):
    array_length = len(array)
    verbose_name = make_agree_with_number(array_length, verbose_names)
    pages_count = (
        array_length // pag_step if array_length / pag_step == array_length // pag_step
        else array_length // pag_step + 1)
    if current_page > pages_count:
        current_page = pages_count
    start = (current_page - 1) * pag_step
    end = current_page * pag_step if current_page * pag_step <= array_length else array_length
    found_phrase = make_agree_with_number(array_length, ['????????????', '??????????????', '??????????????'] if not found_phrases
                                          else found_phrases)
    action_text = context.user_data.get('action_text')
    active, inactive = (action_text['active'], action_text['inactive']) if isinstance(action_text, dict) else (None, None)
    buttons = []
    for entity_id, entity_name in array[start:end]:
        text = (f'{entity_name} ({active if entity_id in context.user_data["selected_ids"] else inactive})' 
                if active and inactive else entity_name)
        buttons.append([InlineKeyboardButton(text, callback_data=entity_id)])
    if pages_count > 1:
        footer = '\n\n<i>?????? ?????????????????? ?????????? ?????????? ?????????????????? ?????????? ????????????????</i>'
        pag_block = [InlineKeyboardButton(f'{current_page}/{pages_count}', callback_data='refresh')]
        if current_page > 1:
            pag_block.insert(0, InlineKeyboardButton('??', callback_data='prev_page'))
        if current_page < pages_count:
            pag_block.append(InlineKeyboardButton('??', callback_data='next_page'))
        buttons.append(pag_block)
    else:
        footer = ''
    if context.user_data.get('extra_buttons') and isinstance(context.user_data['extra_buttons'], list):
        for text, callback_data in context.user_data['extra_buttons']:
            buttons.append([InlineKeyboardButton(text, callback_data=callback_data)])
    if context.user_data.get('site_btn'):
        buttons.append(
            [InlineKeyboardButton('?????????????? ???? ????????',
                                  url=get_config().get('URL ??????????????', {}).get('val', 'https://belberry.net'))])
    buttons.append([InlineKeyboardButton('?????????????????? ??????????', callback_data='back')])
    if not context.user_data.get('messages_to_delete'):
        context.user_data['messages_to_delete'] = []
    context.user_data['messages_to_delete'].append(
        context.bot.send_message(
            context.user_data['id'],
            f'{context.user_data.get("found_prefix", "")}'
            f'{found_phrase} <b>{array_length}</b> {verbose_name}'
            f'{context.user_data.get("found_suffix", "")}{footer}',
            reply_markup=InlineKeyboardMarkup(buttons), parse_mode=ParseMode.HTML).message_id)
    return pages_count


# def build_pagination(context: CallbackContext, array: list,
#                      pag_step: int, current_page: int, verbose_names: list,
#                      sub_category_verbose_name: str, is_sub_already=False,
#                      found_phrases=None):
#     array_length = len(array)
#     verbose_name = make_agree_with_number(array_length, verbose_names)
#     pages_count = (
#         array_length // pag_step if array_length / pag_step == array_length // pag_step
#         else array_length // pag_step + 1)
#     if current_page > pages_count:
#         current_page = pages_count
#     start = (current_page - 1) * pag_step
#     end = current_page * pag_step if current_page * pag_step <= array_length else array_length
#     found_phrase = make_agree_with_number(array_length, ['????????????', '??????????????', '??????????????'] if not found_phrases
#                                           else found_phrases)
#     msg = context.bot.send_message(context.user_data['id'],
#                                    f'{context.user_data.get("found_prefix", "")}'
#                                    f'{found_phrase} <b>{array_length}</b> {verbose_name}'
#                                    f'{context.user_data.get("found_suffix", "")}',
#                                    parse_mode=ParseMode.HTML)
#     context.user_data['messages_to_delete'] = context.user_data.get(
#         'messages_to_delete', []) + [msg.message_id]
#     for d in array[start:end]:
#         d_id = d.pop('id')
#         buttons = []
#         action_text = context.user_data.get('action_text')
#         if isinstance(action_text, dict) and action_text:
#             action_text = action_text['active' if d_id in context.user_data['selected_ids'] else 'inactive']
#         elif not action_text:
#             action_text = '????????????????????'
#         if not is_sub_already:
#             buttons.append([InlineKeyboardButton(sub_category_verbose_name, callback_data=f'{d_id}')])
#         buttons.append([InlineKeyboardButton(action_text, callback_data=f'{d_id} action')])
#         markup = InlineKeyboardMarkup(buttons)
#         try:
#             photo = d.pop('photo')
#         except KeyError:
#             photo = None
#         text = '\n'.join([f'<b>{key}</b>: {val if val else "???? ??????????????"}' for key, val in d.items()])
#         photo_sent = False
#         if photo:
#             try:
#                 msg = context.bot.send_photo(context.user_data['id'], photo, text,
#                                              parse_mode=ParseMode.HTML, reply_markup=markup)
#                 photo_sent = True
#             except BadRequest:
#                 pass
#         if not photo_sent:
#             msg = context.bot.send_message(context.user_data['id'], text,
#                                            parse_mode=ParseMode.HTML, reply_markup=markup)
#         context.user_data['messages_to_delete'].append(msg.message_id)
#     buttons = []
#     if pages_count > 1:
#         pag_block = [InlineKeyboardButton(f'{current_page}/{pages_count}', callback_data='refresh')]
#         if current_page > 1:
#             pag_block.insert(0, InlineKeyboardButton('??', callback_data='prev_page'))
#         if current_page < pages_count:
#             pag_block.append(InlineKeyboardButton('??', callback_data='next_page'))
#         buttons.append(pag_block)
#     if context.user_data.get('extra_buttons') and isinstance(context.user_data['extra_buttons'], list):
#         for text, callback_data in context.user_data['extra_buttons']:
#             buttons.append([InlineKeyboardButton(text, callback_data=callback_data)])
#     if context.user_data.get('site_btn'):
#         buttons.append(
#             [InlineKeyboardButton('?????????????? ???? ????????',
#                                   url=get_config().get('URL ??????????????', {}).get('val', 'https://belberry.net'))])
#     buttons.append([InlineKeyboardButton('?????????????????? ??????????', callback_data='back')])
#     context.user_data['messages_to_delete'].append(
#         context.bot.send_message(
#             context.user_data['id'],
#             '??????????????????. ?????? ???????????????? ???? ???????????????????? ???????????????? ?????????? ?????????????????? ???? ??????????',
#             reply_markup=InlineKeyboardMarkup(
#                 buttons)).message_id)
#     return pages_count


def clear_temp_vars(context: CallbackContext):
    for key in 'selected_ids', 'action_text', 'found_prefix', 'found_suffix', 'extra_buttons':
        if context.user_data.get(key):
            context.user_data.pop(key)


def clear_ids(context: CallbackContext):
    for key in 'specialist_id', 'service_id', 'promotion_id':
        if context.user_data.get(key):
            context.user_data.pop(key)

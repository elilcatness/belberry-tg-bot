import json
import os

from cloudinary import uploader
from telegram.error import BadRequest
from telegram.ext import CallbackContext

from data.db import db_session
from data.db.models.config import Config
from data.db.models.state import State


def delete_last_message(func):
    def wrapper(update, context: CallbackContext):
        if context.user_data.get('message_id'):
            try:
                context.bot.deleteMessage(context.user_data['id'], context.user_data.pop('message_id'))
            except BadRequest:
                pass
        while context.user_data.get('messages_to_delete'):
            context.bot.deleteMessage(context.user_data['id'],
                                      context.user_data['messages_to_delete'].pop(0))
        output = func(update, context)
        if isinstance(output, tuple):
            msg, callback = output
            context.user_data['message_id'] = msg.message_id
            save_state(context.user_data['id'], callback, context.user_data)
        else:
            callback = output
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
        context.bot.edit_message_text(f'{msg_text}{"." * count}', user_id, msg_id)
    context.job.context.user_data['process.count'] = (count + 1) % 4
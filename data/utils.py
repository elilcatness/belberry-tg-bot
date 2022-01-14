import json
import os

from cloudinary import uploader

from telegram.error import BadRequest
from telegram.ext import CallbackContext

from data.db import db_session
from data.db.models.state import State
from data.db.models.config import Config


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


# in front-end: stream = update.message.photo[-1].get_file().download_as_bytearray()

def upload_img(img_stream: bytes):
    return uploader.upload_image(img_stream).url


def delete_img(url: str):
    uploader.destroy(url.split('/')[-1].split('.')[0])
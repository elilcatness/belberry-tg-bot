import json
import os

from telegram import ReplyKeyboardRemove

from data.db import db_session
from data.db.models.callback import Callback
from data.db.models.config import Config
from data.help import help_menu


def save_callback(user_id: int, first_name: str, callback: str, message_id: int = None,
                  register_name: str = None, key_to_change: str = None):
    with db_session.create_session() as session:
        cb = session.query(Callback).filter(Callback.user_id == user_id).first()
        if cb:
            session.delete(cb)
            session.commit()
        session.add(Callback(user_id=user_id, first_name=first_name, callback=callback,
                             message_id=message_id, register_name=register_name,
                             key_to_change=key_to_change))
        session.commit()


def delete_last_message(func):
    def wrapper(update, context):
        if context.user_data.get('message_id'):
            message_id = context.user_data.pop('message_id')
            context.bot.deleteMessage(context.user_data['id'], message_id)
        msg, callback = func(update, context)
        message_id = msg.message_id
        save_callback(context.user_data['id'], context.user_data['first_name'],
                      callback, message_id)
        context.user_data['message_id'] = message_id
        return callback

    return wrapper


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
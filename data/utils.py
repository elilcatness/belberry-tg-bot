import json
import os

from telegram.error import BadRequest

from data.constants import IRREGULAR
from data.db import db_session
from data.db.models.state import State
from data.db.models.config import Config


def handle_last_message(func):
    def wrapper(update, context):
        state = get_current_state(context.user_data['id'])
        if state and state.callback in IRREGULAR:
            context.bot.deleteMessage(context.user_data['id'], context.user_data.pop('message_id'))
        output = func(update, context)
        if isinstance(output, tuple):
            if len(output) == 3:
                args, kwargs, callback = output
            else:
                args, callback = output
                kwargs = dict()
            chat_id, text = args
            send_new = True
            if context.user_data.get('message_id'):
                send_new = False
                try:
                    context.bot.editMessageText(text, chat_id, context.user_data['message_id'], **kwargs)
                except BadRequest:
                    send_new = True
                    try:
                        context.bot.deleteMessage(chat_id, context.user_data.pop('message_id'))
                    except BadRequest:
                        pass
            if send_new:
                context.user_data['message_id'] = context.bot.sendMessage(chat_id, text, **kwargs).message_id
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
import json
import os

from data.db import db_session
from data.db.models.config import Config


def delete_last_message(func):
    def wrapper(update, context):
        if context.user_data.get('message'):
            context.user_data['message'].delete()
        msg, callback = func(update, context)
        context.user_data['message'] = msg
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
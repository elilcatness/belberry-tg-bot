from sqlalchemy import Column, Integer, String

from data.db.db_session import SqlAlchemyBase


class Callback(SqlAlchemyBase):
    __tablename__ = 'callbacks'

    id = Column(Integer, primary_key=True, autoincrement=True, unique=True)
    user_id = Column(Integer, unique=True)
    first_name = Column(String)
    callback = Column(String)
    message_id = Column(Integer, nullable=True)
    register_name = Column(String, nullable=True)
    key_to_change = Column(String, nullable=True)

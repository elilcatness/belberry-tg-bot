from sqlalchemy import Column, Integer, String, Text
from sqlalchemy.orm import relation

from data.db.db_session import SqlAlchemyBase


class Service(SqlAlchemyBase):
    __tablename__ = 'services'

    id = Column(Integer, primary_key=True, autoincrement=True, unique=True)
    name = Column(String, unique=True)
    description = Column(Text, nullable=True)
    photo = Column(String, nullable=True)
    specialists = relation('Specialist', secondary='service_to_specialist', back_populates='services')
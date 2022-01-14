from sqlalchemy import Column, Table, Integer, String, Text, ForeignKey
from sqlalchemy.orm import relation

from data.db.db_session import SqlAlchemyBase


service_to_specialist = Table('service_to_specialist', SqlAlchemyBase.metadata,
                              Column('specialist', Integer, ForeignKey('specialists.id')),
                              Column('service', Integer, ForeignKey('services.id')))


class Specialist(SqlAlchemyBase):
    __tablename__ = 'specialists'

    id = Column(Integer, primary_key=True, autoincrement=True, unique=True)
    full_name = Column(String)
    speciality = Column(String)
    description = Column(Text, nullable=True)
    photo = Column(String, nullable=True)
    services = relation('Service', secondary=service_to_specialist)
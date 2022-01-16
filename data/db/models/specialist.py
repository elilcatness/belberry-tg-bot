from sqlalchemy import Column, Table, Integer, String, Text, ForeignKey
from sqlalchemy.orm import relation

from data.db.db_session import SqlAlchemyBase


service_to_specialist = Table('service_to_specialist', SqlAlchemyBase.metadata,
                              Column('specialist', Integer, ForeignKey('specialists.id')),
                              Column('service', Integer, ForeignKey('services.id')))


class Specialist(SqlAlchemyBase):
    __tablename__ = 'specialists'

    serialize_fields = ('id', 'full_name', 'speciality', 'description', 'photo')
    verbose_names = {'full_name': 'ФИО', 'speciality': 'Специальность', 'description': 'Информация'}

    id = Column(Integer, primary_key=True, autoincrement=True, unique=True)
    full_name = Column(String)
    speciality = Column(String)
    description = Column(Text, nullable=True)
    photo = Column(String, nullable=True)
    services = relation('Service', secondary=service_to_specialist)

    def to_dict(self):
        return {key if key not in self.verbose_names.keys() else self.verbose_names[key]: getattr(self, key)
                for key in self.serialize_fields}
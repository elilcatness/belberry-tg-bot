from sqlalchemy import Column, Integer, String, Text
from sqlalchemy.orm import relation

from data.db.db_session import SqlAlchemyBase


class Service(SqlAlchemyBase):
    __tablename__ = 'services'

    serialize_fields = ('id', 'name', 'description', 'photo')
    verbose_names = {'name': 'Название', 'description': 'Описание'}
    verbose_names_edit = {'name': 'Название', 'photo': 'Фотография', 'specialists': 'Специалисты'}

    id = Column(Integer, primary_key=True, autoincrement=True, unique=True)
    name = Column(String, unique=True)
    description = Column(Text, nullable=True)
    photo = Column(String, nullable=True)
    specialists = relation('Specialist', secondary='service_to_specialist', back_populates='services')

    def to_dict(self):
        return {key if key not in self.verbose_names.keys() else self.verbose_names[key]: getattr(self, key)
                for key in self.serialize_fields}
from sqlalchemy import Column, Integer, String, Table, ForeignKey
from sqlalchemy.orm import relationship

from data.db.db_session import SqlAlchemyBase


class Promotion(SqlAlchemyBase):
    __tablename__ = 'promotions'

    serialize_fields = ('id', 'name', 'description', 'photo')
    verbose_names = {'name': 'Название', 'description': 'Описание'}
    verbose_names_edit = {'name': 'Название', 'photo': 'Фотография', 'services': 'Услуги'}

    id = Column(Integer, primary_key=True, autoincrement=True, unique=True)
    name = Column(String, unique=True)
    description = Column(String)
    photo = Column(String)
    services = relationship('Service', secondary='service_to_promotion', back_populates='promotions')

    def to_dict(self):
        return {key if key not in self.verbose_names.keys() else self.verbose_names[key]: getattr(self, key)
                for key in self.serialize_fields}


service_to_promotion = Table('service_to_promotion', SqlAlchemyBase.metadata,
                             Column('promotion', Integer, ForeignKey('promotions.id')),
                             Column('service', Integer, ForeignKey('services.id')))
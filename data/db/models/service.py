from sqlalchemy import Column, Integer, String, Text, Table, ForeignKey
from sqlalchemy.orm import relationship

from data.db.db_session import SqlAlchemyBase

promotion_to_service = Table('promotion_to_service', SqlAlchemyBase.metadata,
                             Column('service', Integer, ForeignKey('services.id')),
                             Column('promotion', Integer, ForeignKey('promotions.id')))


class Service(SqlAlchemyBase):
    __tablename__ = 'services'

    serialize_fields = ('id', 'name', 'description', 'photo')
    verbose_names = {'name': 'Название', 'description': 'Описание'}
    verbose_names_edit = {'name': 'Название', 'photo': 'Фотография', 'specialists': 'Специалисты'}

    id = Column(Integer, primary_key=True, autoincrement=True, unique=True)
    name = Column(String, unique=True)
    description = Column(Text, nullable=True)
    photo = Column(String, nullable=True)
    specialists = relationship('Specialist', secondary='service_to_specialist')
    promotions = relationship('Promotion', secondary='service_to_promotion')

    def to_dict(self):
        return {key if key not in self.verbose_names.keys() else self.verbose_names[key]: getattr(self, key)
                for key in self.serialize_fields}

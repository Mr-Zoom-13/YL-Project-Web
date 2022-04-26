import datetime
import sqlalchemy
from sqlalchemy import orm
from .db_session import SqlAlchemyBase


class Wastes(SqlAlchemyBase):
    __tablename__ = 'wastes'
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    user_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey('users.id'),
                                index=True)
    community_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey('communities.id'))
    provider_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey('providers.id'))
    category_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey('categories.id'))
    amount = sqlalchemy.Column(sqlalchemy.Integer, nullable=False)
    date = sqlalchemy.Column(sqlalchemy.Date, default=datetime.date.today)
    user = orm.relation('Users')
    provider = orm.relation('Providers')
    category = orm.relation('Categories')
    community = orm.relation('Communities')

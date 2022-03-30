import sqlalchemy
from sqlalchemy import orm
from .db_session import SqlAlchemyBase


class Users(SqlAlchemyBase):
    __tablename__ = 'users'
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    yandex_id = sqlalchemy.Column(sqlalchemy.String, nullable=False, index=True, unique=True)
    name = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    community_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey('communities.id'),
                                     nullable=True)
    limit = sqlalchemy.Column(sqlalchemy.Integer, nullable=True)
    community = orm.relation('Communities')

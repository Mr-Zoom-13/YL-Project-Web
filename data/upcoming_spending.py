import sqlalchemy
from sqlalchemy import orm
from .db_session import SqlAlchemyBase


class Upcoming(SqlAlchemyBase):
    __tablename__ = 'upcoming'
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    user_id = sqlalchemy.Column(sqlalchemy.String, sqlalchemy.ForeignKey('users.id'), index=True)
    amount = sqlalchemy.Column(sqlalchemy.Integer, nullable=False)
    title = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    date = sqlalchemy.Column(sqlalchemy.Date, nullable=False)
    user = orm.relation('Users')

import sqlalchemy
from .db_session import SqlAlchemyBase
from sqlalchemy import orm


class Communities(SqlAlchemyBase):
    __tablename__ = 'communities'
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    title = sqlalchemy.Column(sqlalchemy.String, unique=True, nullable=False)
    team_leader = sqlalchemy.Column(sqlalchemy.Integer)

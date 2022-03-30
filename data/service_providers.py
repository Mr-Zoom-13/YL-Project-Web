import sqlalchemy
from .db_session import SqlAlchemyBase


class Providers(SqlAlchemyBase):
    __tablename__ = 'providers'
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    title = sqlalchemy.Column(sqlalchemy.String, index=True, nullable=False, unique=True)

import sqlalchemy
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class MMUser(Base):
    __tablename__ = "mm_users"

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)  # Mattermost User ID
    created_at = sqlalchemy.Column(sqlalchemy.DateTime)
    update_at = sqlalchemy.Column(sqlalchemy.DateTime)
    delete_at = sqlalchemy.Column(sqlalchemy.DateTime, nullable=True)
    username = sqlalchemy.Column(sqlalchemy.String)
    nickname = sqlalchemy.Column(sqlalchemy.String)
    first_name = sqlalchemy.Column(sqlalchemy.String)
    last_name = sqlalchemy.Column(sqlalchemy.String)


meta = Base.metadata

from app import db, session, Base
from sqlalchemy.orm import relationship
from flask_jwt_extended import create_access_token
from datetime import timedelta
from passlib.hash import bcrypt
class Video(Base):
    __tablename__ = 'videos'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    name = db.Column(db.String(250), nullable=False)
    description = db.Column(db.String(500), nullable=False)


class User(Base):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(250), nullable=False)
    email = db.Column(db.String(250), nullable=False, unique=True)
    password = db.Column(db.String(100), nullable=False)
    videos = relationship('Video', backref='user', lazy=True)


    def __init__(self, **kwargs):
        self.name = kwargs.get('name')
        self.email = kwargs.get('email')
        self.password = bcrypt.hash(kwargs.get('password'))

    def get_token(self, expire_time=24):
        expire_delta = timedelta(expire_time)
        token = create_access_token(
            identity=self.id,
            expires_delta=expire_delta
        )
        return token

    @classmethod
    def authenticate(cls, email, password):
        # 1. email을 unique필드로서 user객체를 one으로 찾는다.
        user = cls.query.filter(cls.email == email).one()
        # 2. user속 해쉬비밀번호 vs 들어온 비밀번호를 bcrypt패키지를 이용해서 확인하여 틀리면
        #    raise 한다.
        if not bcrypt.verify(password, user.password):
            raise Exception(f'No user with this password')
        # 3. 비밀번호가 일치하면, user개체를 반환한다
        return user
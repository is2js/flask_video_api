from . import db, session, Base
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

    @classmethod
    def get_list(cls, user_id):
        try:
            # 1. 바로 return 쿼리.결과()가 아니라 => 변수로 추출 + TA session처리 in try만 하고, 성공시 raise안걸리고 return되게 한다
            videos = cls.query.filter(cls.user_id == user_id).all()
            session.close()
        except Exception:
            # 2. 모델.query의 조회session과 일치하는 scoped_session을 rollback후 바깥에서 잡히도록 raise한다
            session.rollback()
            raise
        return videos

    def save(self):
        try:
            session.add(self)
            session.commit()
        except Exception:
            session.rollback()
            raise

    @classmethod
    def get(cls, tutorial_id, user_id):
        try:
            video = cls.query.filter(
                cls.id == tutorial_id,
                cls.user_id == user_id
            ).first()
            if not video:
                # return {'message': 'No tutorials with this id'}, 404
                raise Exception('No tutorials with this id')

            # 개별이후 update가 이루어질 것이라서, TR session을 닫는 것을 보류한다.
        except Exception:
            session.rollback()
            raise
        return video

    def update(self, **kwargs):
        try:
            for key, value in kwargs.items():
                setattr(self, key, value)
            session.commit()
        except Exception:
            session.rollback()
            raise
    def delete(self):
        try:
            session.delete(self)
            session.commit()
        except Exception:
            session.rollback()
            raise


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

    def save(self):
        try:
            session.add(self)
            session.commit()
        except Exception:
            session.rollback()
            raise
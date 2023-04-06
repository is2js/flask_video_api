import logging
import os.path

from flask import Flask
import sqlalchemy as db
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from flask_jwt_extended import JWTManager

from .config import Config
from flask_apispec.extension import FlaskApiSpec
from apispec import APISpec
from apispec.ext.marshmallow import MarshmallowPlugin

from .schemas import VideoSchema, UserSchema, AuthSchema

app = Flask(__name__)

# config
app.config.from_object(Config)
app.config.update({
    'APISPEC_SPEC': APISpec(
        title='videoblog',  # [swagger-ui] 제목
        version='v1',  # [swagger-ui] 버전
        openapi_version='2.0',  # swagger 자체 버전
        plugins=[MarshmallowPlugin()]
    ),
    'APISPEC_SWAGGER_URL': '/swagger/'  # swagger 자체 정보 url
})

# test
client = app.test_client()
# extensions -> app객체에 bp등록보다 더 아래로 app정보로 초기화하는 코드 이동
jwt = JWTManager()
docs = FlaskApiSpec()
# docs.init_app(app)

engine = create_engine('sqlite:///db.sqlite')

session = scoped_session(sessionmaker(
    autocommit=False, autoflush=False, bind=engine
))

Base = declarative_base()
Base.query = session.query_property()
# models.py가 import한 Base보다 더 밑에서 import된다.
# create_all 전에 메모리에 models들이 떠있어야한다.
from .models import *

Base.metadata.create_all(bind=engine)


# logger
def setup_logger():
    # 1. logger객체를 만들고, 수준을 정해준다.
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)

    # 2. formatter를 작성한다
    formatter = logging.Formatter('%(asctime)s:%(name)s:%(levelname)s:%(message)s')

    # 3. 로그 파일을 지정 handler를 만들고, formatter를 지정해준 뒤, logger객체에 handler에 추가한다.
    # file_handler = logging.FileHandler('log/api.log')
    # - 폴더가 없으면 FileNotFoundError가 나므로 미리 만들거나 없으면 만들어줘야한다.
    LOG_FOLDER = 'log/'

    # 나중에는 LOG_FOLDER = os.path.join(BASE_FOLDER, 'log/')
    if not os.path.exists(LOG_FOLDER):
        os.mkdir(LOG_FOLDER)
    file_handler = logging.FileHandler(os.path.join(LOG_FOLDER, 'api.log'))
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger


logger = setup_logger()


@app.teardown_appcontext
def shutdown_session(exception=None):
    session.remove()


from .user.views import users
from .main.views import videos

app.register_blueprint(users)
app.register_blueprint(videos)

# extension init  after app에 bp등록 이후
docs.init_app(app)
jwt.init_app(app)

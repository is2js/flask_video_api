import logging
import os.path

from flask import Flask, jsonify
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from flask_jwt_extended import JWTManager, jwt_required, get_jwt_identity

import models
from config import Config
from flask_apispec.extension import FlaskApiSpec
from apispec import APISpec
from apispec.ext.marshmallow import MarshmallowPlugin
from flask_apispec import marshal_with, use_kwargs

from schemas import VideoSchema, UserSchema, AuthSchema

app = Flask(__name__)
# config
app.config.from_object(Config)
models.update({
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

# extensions
jwt = JWTManager(app)
docs = FlaskApiSpec()
docs.init_app(app)

engine = create_engine('sqlite:///db.sqlite')

session = scoped_session(sessionmaker(
    autocommit=False, autoflush=False, bind=engine
))

Base = declarative_base()
Base.query = session.query_property()
# models.py가 import한 Base보다 더 밑에서 import된다.
# create_all 전에 메모리에 models들이 떠있어야한다.
from models import *

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

@app.route('/tutorials', methods=['GET'])
@jwt_required()
@marshal_with(VideoSchema(many=True))
def get_list():
    try:
        user_id = get_jwt_identity()
        videos = Video.get_list(user_id=user_id)
    except Exception as e:
        logger.warning(
            f'user: {user_id} tutorials - read action failed with errors: {e}'
        )
        return [{'message': str(e)}], 400
    return videos


@app.route('/tutorials', methods=['POST'])
@jwt_required()
@use_kwargs(VideoSchema)
@marshal_with(VideoSchema)
def update_list(**kwargs):
    try:
        user_id = get_jwt_identity()
        new_one = Video(user_id=user_id, **kwargs)
        new_one.save()
    except Exception as e:
        logger.warning(
            f'user: {user_id} tutorial - create action failed with errors: {e}'
        )
        return {'message': str(e)}, 400
    return new_one


@app.route('/tutorials/<int:tutorial_id>', methods=['PUT'])
@jwt_required()
@use_kwargs(VideoSchema)
@marshal_with(VideoSchema)
def update_tutorial(tutorial_id, **kwargs):
    try:
        user_id = get_jwt_identity()

        # 개별조회 + 확인로직
        item = Video.get(tutorial_id, user_id)
        # update로직 -> **kwargs를 인자에 유지하면, [키워드입력]이 된다
        item.update(**kwargs)

    except Exception as e:
        logger.warning(
            f'user: {user_id} tutorial:{tutorial_id} - update action failed with errors: {e}'
        )
        return {'message': str(e)}, 400
    return item


@app.route('/tutorials/<int:tutorial_id>', methods=['DELETE'])
@jwt_required()
@marshal_with(VideoSchema)
def delete_tutorial(tutorial_id):
    try:
        user_id = get_jwt_identity()
        item = Video.get(tutorial_id, user_id)
        item.delete()
    except Exception as e:
        logger.warning(
            f'user: {user_id} tutorial:{tutorial_id} - delete action failed with errors: {e}'
        )
        return {'message': str(e)}, 400
    return '', 204


@app.route('/register', methods=['POST'])
@use_kwargs(UserSchema)
@marshal_with(AuthSchema)
def register(**kwargs):
    try:
        user = User(**kwargs)
        user.save()
        token = user.get_token()
    except Exception as e:
        logger.warning(
            f'registration failed with errors: {e}'
        )
        return {'message': str(e)}, 400
    return {'access_token': token}


@app.route('/login', methods=['POST'])
@use_kwargs(UserSchema(only=('email', 'password')))  # only 미작성시 register payload기준에 못미쳐서 422 뜸.
@marshal_with(AuthSchema)
def login(**kwargs):
    try:
        user = User.authenticate(**kwargs)
        token = user.get_token()
    except Exception as e:
        logger.warning(
            f'login with email{kwargs["email"]} failed with errors: {e}'
        )
        return {'message': str(e)}, 400
    return {'access_token': token}


@app.teardown_appcontext
def shutdown_session(exception=None):
    session.remove()


@app.errorhandler(422)
def error_handler(err):
    # error는 werkzeug.exceptions에 있는 (422)에 대한 entity가 내려온다.
    # 만약 code를 지정하지 않으면, 인자에는 status가 내려오며
    #  -> 직접 from werkzeug.exceptions import Forbidden, Unauthorized을 import해서 정보를 나열해야한다.
    # 참고: https://github.com/zain2323/docterlyapi/blob/main/api/auth/authentication.py
    # typo(err) >>> <class 'werkzeug.exceptions.UnprocessableEntity'>
    #               code, name, description, data

    # 하지만, [err.data]에 들어가야지만, marshmallow가 내려준 상세 에러정보를 볼 수 있다.
    # -> headers, messages, schema
    # {'messages': {'json': {'name': ['Missing data for required field.'], 'description': ['Missing data for required field.']}}, 'schema': <VideoSchema(many=False)>, 'headers': None}

    # 1. 422에러를 일으킬 때의 header정보를 가져온다.
    headers = models.get('headers', None)

    # 2. 422에러 발생시 인자에서 'messages'(list)를 주므로 message도 가져온다.
    #   - 없을 경우 defaultt 에러message list를 반환한다.
    messages = models.get('messages', ['Invalid request'])
    # 4. 로그도 찍어준다.
    logger.warning(
        f'Invalid input params: {messages}'
    )
    # 3. header정보가 있다면, tuple 3번째 인자로 같이 반환한다
    if headers:
        return jsonify({'message': messages}), 400, headers
    else:
        return jsonify({'message': messages}), 400


# docs register view_functions
docs.register(get_list)
docs.register(update_list)
docs.register(update_tutorial)
docs.register(delete_tutorial)
docs.register(register)
docs.register(login)

if __name__ == '__main__':
    app.run(host='127.0.0.1', port='5000')

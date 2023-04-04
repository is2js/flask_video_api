from flask import Flask, jsonify, request
import sqlalchemy as db  # 각 model들이 Column 등 정의시 갖다 씀.
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from flask_jwt_extended import JWTManager, jwt_required, get_jwt_identity
from config import Config
from flask_apispec.extension import FlaskApiSpec
from apispec import APISpec
from apispec.ext.marshmallow import MarshmallowPlugin
from flask_apispec import marshal_with, use_kwargs

from schemas import VideoSchema, UserSchema, AuthSchema

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


@app.route('/tutorials', methods=['GET'])
@jwt_required()
@marshal_with(VideoSchema(many=True))
def get_list():
    # return jsonify(tutorials)
    # videos = Video.query.all()
    user_id = get_jwt_identity()
    videos = Video.query.filter(Video.user_id == user_id).all()

    """
    serialized = []
    for video in videos:
        serialized.append({
            'id': video.id,
            'user_id': video.user_id,
            'name': video.name,
            'description': video.description,
        })
    return jsonify(serialized)
    """
    # .dump될 대상이 객체list(컬렉션)이라면, many=True옵션을 준다.
    # schema = VideoSchema(many=True)
    # return jsonify(schema.dump(videos))

    return videos


@app.route('/tutorials', methods=['POST'])
@jwt_required()
# def update_list():
@use_kwargs(VideoSchema)
@marshal_with(VideoSchema)
def update_list(**kwargs):
    # new_one = Video(**request.json)

    # @jwt_required()를 통과하면, flask의 g변수에 token정보를 집어넣어놓고 잇는데,
    # get_jwt_identity를 통해, token생성시 사용된 identity = self(user).id를 다시 반환해준다.
    user_id = get_jwt_identity()
    # new_one = Video(user_id=user_id, **request.json)
    new_one = Video(user_id=user_id, **kwargs)

    session.add(new_one)
    session.commit()

    # serialized = {
    #     'id': new_one.id,
    #     'user_id': new_one.user_id,
    #     'name': new_one.name,
    #     'description': new_one.description,
    # }
    # return jsonify(serialized)
    return new_one


@app.route('/tutorials/<int:tutorial_id>', methods=['PUT'])
@jwt_required()
@use_kwargs(VideoSchema)
@marshal_with(VideoSchema)
def update_tutorial(tutorial_id, **kwargs):
    user_id = get_jwt_identity()
    item = Video.query.filter(
        Video.id == tutorial_id,
        Video.user_id == user_id
    ).first()
    # params = request.json
    if not item:
        return {'message': 'No tutorials with this id'}, 404

    # for key, value in params.items():
    for key, value in kwargs.items():
        setattr(item, key, value)
    session.commit()

    # serialized = {
    #     'id': item.id,
    #     'user_id': item.user_id,
    #     'name': item.name,
    #     'description': item.description,
    # }
    # return serialized
    return item


@app.route('/tutorials/<int:tutorial_id>', methods=['DELETE'])
@jwt_required()
@marshal_with(VideoSchema)
def delete_tutorial(tutorial_id):
    user_id = get_jwt_identity()
    item = Video.query.filter(
        Video.id == tutorial_id,
        Video.user_id == user_id
    ).first()

    if not item:
        return {'message': 'No tutorials with this id'}, 404

    session.delete(item)
    session.commit()
    return '', 204


@app.route('/register', methods=['POST'])
@use_kwargs(UserSchema)
@marshal_with(AuthSchema)
def register(**kwargs):
    # params = request.json
    # user = User(**params)
    user = User(**kwargs)
    # 1. 회원정보로 -> User모델 객체를 만들고 -> session.add해서 저장한다.
    session.add(user)
    session.commit()
    # 2. 회원이 등록되면, 로그인 한것으로 간주하여 -> 그 때 token을 발급한다.
    token = user.get_token()
    # 3. 응답시 'access_token' key로 내려보낸다
    return {'access_token': token}


@app.route('/login', methods=['POST'])
@use_kwargs(UserSchema(only=('email', 'password'))) # only 미작성시 register payload기준에 못미쳐서 422 뜸.
@marshal_with(AuthSchema)
def login(**kwargs):
    # params = request.json
    # params에는 email/password 2개가 인증=로그인에 필요한 정보로서 들어온다
    # -> 로그인(인증)메서드에 **로 dict unpacking해서,
    # -> args로 정의했지만 변수명에 맞게 자등으로 들어간다.

    # 1. 인증메서드 = 조회 + 로그인 확인 후 반환까지 한번에 해주니, user로 받는다.
    # user = User.authenticate(**params)
    user = User.authenticate(**kwargs)
    # 2. 로그인 성공시, token을 발급하여 반환한다.
    token = user.get_token()
    return {'access_token': token}


@app.teardown_appcontext
def shutdown_session(exception=None):
    session.remove()


# docs register view_functions
docs.register(get_list)
docs.register(update_list)
docs.register(update_tutorial)
docs.register(delete_tutorial)
docs.register(register)
docs.register(login)

if __name__ == '__main__':
    app.run(host='127.0.0.1', port='5000')

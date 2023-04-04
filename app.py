from flask import Flask, jsonify, request
import sqlalchemy as db  # 각 model들이 Column 등 정의시 갖다 씀.
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from flask_jwt_extended import JWTManager, jwt_required, get_jwt_identity

from config import Config

app = Flask(__name__)
app.config.from_object(Config)
client = app.test_client()

# extensions
jwt = JWTManager(app)

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
def get_list():
    # return jsonify(tutorials)
    # videos = Video.query.all()
    user_id = get_jwt_identity()
    videos = Video.query.filter(
        Video.user_id == user_id
    ).all()

    serialized = []
    for video in videos:
        serialized.append({
            'id': video.id,
            'user_id': video.user_id,
            'name': video.name,
            'description': video.description,
        })
    return jsonify(serialized)


@app.route('/tutorials', methods=['POST'])
@jwt_required()
def update_list():
    # new_one = Video(**request.json)

    # @jwt_required()를 통과하면, flask의 g변수에 token정보를 집어넣어놓고 잇는데,
    # get_jwt_identity를 통해, token생성시 사용된 identity = self(user).id를 다시 반환해준다.
    user_id = get_jwt_identity()
    new_one = Video(user_id=user_id, **request.json)

    session.add(new_one)
    session.commit()

    serialized = {
        'id': new_one.id,
        'user_id': new_one.user_id,
        'name': new_one.name,
        'description': new_one.description,
    }

    return jsonify(serialized)


@app.route('/tutorials/<int:tutorial_id>', methods=['PUT'])
@jwt_required()
def update_tutorial(tutorial_id):
    # item = next((x for x in tutorials if x['id'] == tutorial_id), None)
    # item = Video.query.filter(Video.id == tutorial_id).first()
    user_id = get_jwt_identity()
    item = Video.query.filter(
        Video.id == tutorial_id,
        Video.user_id == user_id
    ).first()
    params = request.json
    if not item:
        return {'message': 'No tutorials with this id'}, 404

    # item.update(params)
    # return item

    # dictionary 업데이트 -> 객체 업데이트로 변경될 시
    # -> 1. params(payload)를 Model.query조회된 객체에 fill(setattr)을 직접 해줘야한다.
    #       => 조회하고 난 뒤, scoped_session에 캐싱되어있는 것 같다.(객체생성시는 session.add( 순수obj))
    #       print(session.identity_map.values())
    #       [<models.Video object at 0x00000242C10B5490>]
    #       => Model.query로 조회된 객체는 session에 캐싱되어있다.
    # -> 2. session으로 add없이 commit()만 해주면, 변경내역이 자동반영된다.
    for key, value in params.items():
        setattr(item, key, value)
    session.commit()

    serialized = {
        'id': item.id,
        'user_id': item.user_id,
        'name': item.name,
        'description': item.description,
    }
    return serialized


@app.route('/tutorials/<int:tutorial_id>', methods=['DELETE'])
@jwt_required()
def delete_tutorial(tutorial_id):
    # idx, _ = next(((idx, x) for idx, x in enumerate(tutorials) if x['id'] == tutorial_id), (None, None))
    # if idx is None:
    #     return {'message': 'No tutorials with this id'}, 404
    # tutorials.pop(idx)
    # return '', 204

    # item = Video.query.filter(Video.id == tutorial_id).first()
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
def register():
    params = request.json
    # 1. 회원정보로 -> User모델 객체를 만들고 -> session.add해서 저장한다.
    user = User(**params)
    session.add(user)
    session.commit()
    # 2. 회원이 등록되면, 로그인 한것으로 간주하여 -> 그 때 token을 발급한다.
    token = user.get_token()
    # 3. 응답시 'access_token' key로 내려보낸다
    return {'access_token': token}


@app.route('/login', methods=['POST'])
def login():
    params = request.json
    # params에는 email/password 2개가 인증=로그인에 필요한 정보로서 들어온다
    # -> 로그인(인증)메서드에 **로 dict unpacking해서,
    # -> args로 정의했지만 변수명에 맞게 자등으로 들어간다.

    # 1. 인증메서드 = 조회 + 로그인 확인 후 반환까지 한번에 해주니, user로 받는다.
    user = User.authenticate(**params)
    # 2. 로그인 성공시, token을 발급하여 반환한다.
    token = user.get_token()
    return {'access_token': token}


@app.teardown_appcontext
def shutdown_session(exception=None):
    session.remove()


if __name__ == '__main__':
    app.run(host='127.0.0.1', port='5000')

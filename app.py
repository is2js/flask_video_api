from flask import Flask, jsonify, request
import sqlalchemy as db
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base

app = Flask(__name__)

client = app.test_client()

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

tutorials = \
    [
        {
            'id': 1,
            'title': 'Video #1. Intro',
            'description': 'GET, POST routes',
        },
        {
            'id': 2,
            'title': 'Video #2. More features',
            'description': 'PUT, DELETE routes',
        },
    ]


@app.route('/tutorials', methods=['GET'])
def get_list():
    # return jsonify(tutorials)
    videos = Video.query.all()
    serialized = []
    for video in videos:
        serialized.append({
            'id': video.id,
            'name': video.name,
            'description': video.description,
        })
    return jsonify(serialized)


@app.route('/tutorials', methods=['POST'])
def update_list():
    # new_one = request.json
    # tutorials.append(new_one)
    # return jsonify(tutorials)
    new_one = Video(**request.json)
    session.add(new_one)
    session.commit()

    serialized = {
        'id': new_one.id,
        'name': new_one.name,
        'description': new_one.description,
    }

    return jsonify(serialized)


@app.route('/tutorials/<int:tutorial_id>', methods=['PUT'])
def update_tutorial(tutorial_id):
    # item = next((x for x in tutorials if x['id'] == tutorial_id), None)
    item = Video.query.filter(Video.id == tutorial_id).first()
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
        'name': item.name,
        'description': item.description,
    }
    return serialized


@app.route('/tutorials/<int:tutorial_id>', methods=['DELETE'])
def delete_tutorial(tutorial_id):
    # idx, _ = next(((idx, x) for idx, x in enumerate(tutorials) if x['id'] == tutorial_id), (None, None))
    # if idx is None:
    #     return {'message': 'No tutorials with this id'}, 404
    # tutorials.pop(idx)
    # return '', 204
    item = Video.query.filter(Video.id == tutorial_id).first()
    if not item:
        return {'message': 'No tutorials with this id'}, 404

    session.delete(item)
    session.commit()
    return '', 204



@app.teardown_appcontext
def shutdown_session(exception=None):
    session.remove()


if __name__ == '__main__':
    app.run()

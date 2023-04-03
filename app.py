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
    return jsonify(tutorials)


@app.route('/tutorials', methods=['POST'])
def update_list():
    new_one = request.json
    tutorials.append(new_one)
    return jsonify(tutorials)


@app.route('/tutorials/<int:tutorial_id>', methods=['PUT'])
def update_tutorial(tutorial_id):
    item = next((x for x in tutorials if x['id'] == tutorial_id), None)
    params = request.json
    if not item:
        return {'message': 'No tutorials with this id'}, 404

    item.update(params)

    return item


@app.route('/tutorials/<int:tutorial_id>', methods=['DELETE'])
def delete_tutorial(tutorial_id):
    idx, _ = next(((idx, x) for idx, x in enumerate(tutorials) if x['id'] == tutorial_id), (None, None))
    # if not idx:
    if idx is None:
        return {'message': 'No tutorials with this id'}, 404
    tutorials.pop(idx)
    return '', 204

@app.teardown_appcontext
def shutdown_session(exception=None):
    session.remove()

if __name__ == '__main__':
    app.run()

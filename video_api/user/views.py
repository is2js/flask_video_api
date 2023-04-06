from flask import Blueprint, jsonify
from flask_apispec import use_kwargs, marshal_with

from video_api import logger, docs
from video_api.schemas import UserSchema, AuthSchema
from video_api.models import User

users = Blueprint('users', __name__)

# @app.route('/register', methods=['POST'])
@users.route('/register', methods=['POST'])
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


@users.route('/login', methods=['POST'])
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


@users.errorhandler(422)
def error_handler(err):
    headers = err.data.get('headers', None)
    messages = err.data.get('messages', ['Invalid request'])

    logger.warning(f'Invalid input params: {messages}')

    if headers:
        return jsonify({'message': messages}), 400, headers
    else:
        return jsonify({'message': messages}), 400

docs.register(register, blueprint='users')
docs.register(login, blueprint='users')

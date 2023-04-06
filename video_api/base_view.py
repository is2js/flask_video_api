from flask import jsonify
from flask_apispec.views import MethodResource

# 1. apispec 모듈은 flask.views.MethodView를 상속한 모듈로서
#    - MethodView대신 apispec 기능이 부가된 MethodView를 상속한다고 생각한다.
class BaseView(MethodResource):

    @classmethod
    def register(cls, blueprint, spec, url, name):
        # 2. 해당url + name으로 bp에 view를 등록한다.
        blueprint.add_url_rule(url, view_func=cls.as_view(name))
        # 3. 공통 에러핸들링 422에러를 bp에 등록한다
        blueprint.register_error_handler(422, cls.handle_error)
        # 4. 해당bp이름으로 docs에 view class(기존 route view func)을 등록한다
        spec.register(cls, blueprint=blueprint.name)

    @staticmethod
    def handle_error(err):
        headers = err.data.get('headers', None)
        messages = err.data.get('messages', ['Invalid request'])
        if headers:
            return jsonify({'message': messages}), 400, headers
        else:
            return jsonify({'message': messages}), 400

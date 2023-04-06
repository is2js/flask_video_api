1. api(`video_api`)모듈의 root에 view class마다 공통작업을 명시할 `base_view.py`를 만든다
2. flask원본의 `MethodView`에 기능을 더한 `flask_apispec.views의 MethodResource`를 통해 view class를 구성한다
   - 이를 상속한 클래스는 @classmethod의 인자로 `등록할 bp, spec, url, name`을 받아서
     1. `bp`에 `url` + 해당view`cls`를 view_func으로 바꿔주는 `.as_view`( `name` )으로 url_rule을 add한다
     2. `bp`에 특정에러 422에 대해서,  `공통 에러핸들링 등록메서드`로 등록해준다.
        - 이 때, 아래에서 추가로 cls.hanlder_error를 @staticmehotd로 작성해줄 것이다.
     3. `spec(docs)`에 해당 bp이름으로 현재 view class를 등록한다(원래는 route view func 등록 with bp이름)
   ```python
   # video_api/base_view.py
   
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
   
   ```
   

3. cls를 이용하지 않는 `@staticmethod`로 cls.handler error를 해준다.
    ```python
        @staticmethod
        def handle_error(err):
            headers = err.data.get('headers', None)
            messages = err.data.get('messages', ['Invalid request'])
            if headers:
                return jsonify({'message': messages}), 400, headers
            else:
                return jsonify({'message': messages}), 400
    
    ```

   
4. 각 하위모듈의 views.py에서 상위모듈아래.base_view(.py)의 `BaseView`를 import하고, 상속해서 route급의 view class를 작성해준다.
    - BaseView로 작성된 View class(route대체)는 에러핸들링 + docs 등이 상속된, BaseView에 정의한 `.register()`메서드로 한방에 등록할 수 있다.
      1. `video_api/users/views.py`
    ```python
    #...
    from video_api.base_view import BaseView
    #...
    class ProfileView(BaseView):
        #  get route 내용을 작성한다. 데코레이터도 여기서 단다
        @jwt_required()
        @marshal_with(UserSchema)
        def get(self):
            user_id = get_jwt_identity()
            try:
                user = User.query.get(user_id)
                if not user:
                    raise Exception('User not found')
            except Exception as e:
                logger.warning(
                    f'user: {user_id} failed to read profile: {e}'
                )
            return user
    
    #...
    
    docs.register(register, blueprint='users')
    docs.register(login, blueprint='users')
    ProfileView.register(users, docs, '/profile', 'profileview')
    ```
    - console 테스트
    ```python
    from video_api import client
    email_ = 'test@gmail.com'
    password_ = '1234'
    login = client.post('login', json=dict(email=email_, password=password_))
    token = login.get_json()['access_token']
    auth_header = dict(Authorization=f'Bearer {token}')
    res = client.get('/profile', headers=auth_header)
    
    res.get_json()
    # {'email': 'test@gmail.com', 'name': 'test user', 'videos': [{'description': '1234', 'id': 1, 'name': 'New Video', 'user_id': 1}, {'description': '1234', 'id': 2, 'name': 'New Video', 'user_id': 1}, {'description': '직렬화/역직렬화', 'id': 3, 'name': 'Flask-Apispec', 'user_id': 1}]}
    ```
   
5. 이제 422에러 핸들링을 bp마다 개별로 안지정해줘도, 자동으로 포함된다.
    ```python
    # @users.errorhandler(422)
    # def error_handler(err):
    #     headers = err.data.get('headers', None)
    #     messages = err.data.get('messages', ['Invalid request'])
    #
    #     logger.warning(f'Invalid input params: {messages}')
    #
    #     if headers:
    #         return jsonify({'message': messages}), 400, headers
    #     else:
    #         return jsonify({'message': messages}), 400
   
    ProfileView.register(users, docs, '/profile', 'profileview')
    ```
    - console에서 parameter 이상하게 주고 422 테스트
    ```python
    from video_api import client
    email_ = 'test@gmail.com'
    password_ = '1234'
    login = client.post('login', json=dict(email=email_, password=password_))
    token = login.get_json()['access_token']
    auth_header = dict(Authorization=f'Bearer {token}')
    res = client.post('/login', headers=auth_header, json={})
    
    res
    # <WrapperTestResponse streamed [400 BAD REQUEST]>
    res.get_json()
    # {'message': {'json': {'email': ['Missing data for required field.'], 'password': ['Missing data for required field.']}}}
    
    ```
   
6. 특정유저의 전체목록 조회 `/tutorials`(.get_user_list()) 대신 누구간 볼 수 있는 전체목록 조회 `/main` (.get_list())url로 vidos/views.py를 BaseView 상속으로 구현해보자.
   1. 틀 잡기
       ```python
       videos = Blueprint('videos', __name__)
     
       class ListView(BaseView):
           @marshal_with(VideoSchema(many=True))
           def get(self):
               try:
                   ...
               except Exception as e:
                   logger.warning(
                       f''
                   )
                   return[{'message': str(e)}], 400
               return 
     
       ListView.register(videos, docs, '/main', 'listview')
       ```
   2. 조회라도, @classmethod로 래핑해서 session을 처리 or rollback시킨다
       ```python
       class ListView(BaseView):
           @marshal_with(VideoSchema(many=True))
           def get(self):
               try:
                   videos = Video.get_list()
               except Exception as e:
                   logger.warning(
                       f'videos - read action with errors: {e}'
                   )
                   return[{'message': str(e)}], 400
               return videos
       ```
   3. cls로 조회메서드 작성(try 조회후 session닫기 / except rollback후 raise Exception으로 메세지 바깥으로 던져주기)
       ```python
       @classmethod
       def get_list(cls):
           try:
               videos = cls.query.all()
               session.close()
           except Exception:
               session.rollback()
               raise
           return videos
       ```
   4. console 테스트(인증 정보없이 바로 호출)
       ```python
       from video_api import client
       
       res = client.get('/main')
       res.get_json()
       # [{'description': '1234', 'id': 1, 'name': 'New Video', 'user_id': 1}, {'description': '1234', 'id': 2, 'name': 'New Video', 'user_id': 1}, {'description': '직렬화/역직렬화', 'id': 3, 'name': 'Flask-Apispec', 'user_id': 1}]
       ``` 
    

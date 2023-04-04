### 질답
- flask-marshmallow를 사용해 SQLAlchemyAutoSchema를 통한 자동 직렬화/역직렬화 하지 않는 이유는?
  - 자동 체계의 문제점은 항상 필요한 방식으로 생성되지 않는다는 것입니다. apispec은 경로에서 데이터를 직렬화/역직렬화하는 데 사용
  - `apispec의 편리함`은 `스키마로 덤프 및 로드 작업을 수동으로 수행할 필요가 없다는 것`입니다. 이 논리는 `apispec 데코레이터`에 있습니다. 또한 `apispec은 swagger 문서를 생성`
- flask-marshmallow가 아닌 ​​marshmallow로 작업하는 이유를 설명해 주시겠습니까?
  - 이 애플리케이션에서 필요한 것은 `스키마`를 통해 `데이터를 직렬화, 역직렬화, 검증`하는 것뿐입니다. 이 기능을 위해서는 마시멜로면 충분합니다.
  - `"순수한" 마시멜로를 사용하면 십진수를 문자열로 변환`할 수 있습니다. 너무 나쁜 flask-marshmallow는 그것을 허용하지 않습니다
-  IF...ELSE 분기를 통해 하나의 함수에 루트가 있는 경우. 이 apispec이 표시됩니다. 하지만! 왜냐하면 @marshal_with는 전체 루트에 대해 하나의 공통으로 설정되며 그 설명은 두 방법 모두에 적용됩니다. 각 방법에 대한 설명을 별도로 작성하는 방법은 무엇입니까?
  - 개체 목록을 발급하는 GET과 하나의 개체를 발급하는 POST/PUT/DELETE가 있으면 모든 곳에서 many=True 매개변수가 필요하기 때문에 각 메서드를 별도로 작성해야 합니다(클래스 옵션으로 각 메소드 앞에 @marshal_with를 작성할 수 있습니다 .
  - 클래스를 사용하거나 적어도 GET, POST, ...에 대한 논리를 별도의 기능으로 분리합니다. 그런 다음 각각에 대해 marshal_with 및 @doc(description=...) 둘 다 설정할 수 있습니다.
### 내용
1. `marshmallow`, `flask-apispec` 패키지 설치하기

2. `app.py`에서 `/swagger-ui`를 붙이기 위해 `FlaskApiSpec`모듈 가져와 초기화하기
    ```python
    from flask_apispec.extension import FlaskApiSpec
    
    #...
    
    # extensions
    jwt = JWTManager(app)
    docs = FlaskApiSpec()
    docs.init_app(app)
    ```
   - 서버 재실행 후 `http://127.0.0.1:5000/swagger-ui/`를 접속한다
        ![img.png](./images/swagger_ui.png)

3. `app.py`에서, swagger(APISpec)에 대한 설정을 MarshMallow와 연계하기 위해
   - 같이 설치되는 원본 `apispec`패키지의 `MarshmallowPlugin` 모듈과 `APISpec`모듈 가져와서 conifg 걸어주기
   - `docs.init_app(app)`보다 더 위 쪽에서 app에 먼저 config로 걸어야한다.
    ```python
    from apispec import APISpec
    from apispec.ext.marshmallow import MarshmallowPlugin
    # ...
    app.config.from_object(Config)
    app.config.update({
        'APISPEC_SPEC': APISpec(
            title='videoblog',  # [/swagger-ui] 제목
            version='v1',  # [/swagger-ui] 버전
            openapi_version='2.0',  # swagger 자체 버전
            plugins=[MarshmallowPlugin()]
        ),
        'APISPEC_SWAGGER_URL': '/swagger/'  # swagger 자체 정보 url
    })
   
    # ...
    docs = FlaskApiSpec()
    docs.init_app(app)
    ```
   - `APISPEC_SWAGGER_URL`에 해당하는 `/swagger`에 접속하면, 설정한 swagger 정보를 확인할 수 있다.
      - `http://127.0.0.1:5000/swagger/`
      ```json
      info:	
          title:	"videoblog"
          version:	"v2"
      paths:	{}
      swagger:	"2.0"
      ```
4. root에 `schemas.py` 생성하여 Marshmallow 사용하기
   - Schema와 fileds는 class를 정의, validate는 model필드들의 조건(ex>String(250))을 정의한다.
     - `"dump_only"`는 Serializer에서 Serialize 할 때만 필드가 사용되도록 지정합니다. 즉, Deserialize 시 필드를 무시합니다.
       - id, fk는 내려보내줄 땐 넣어주고, request.json(payload)로부터 받을 땐 빼고 받는다는 말인 듯.
       - id는 token에서, fk는 url path를 통해 얻으므로?
   ```python
    # schemas.py
    from marshmallow import Schema, fields, validate
    
    class VideoSchema(Schema):
        # id와 fk는 payload에서 받지않고, token/url_path로부터 받을 것이므로, 역직렬화(view->back)에서는 안받도록 해준다.
        id = fields.Integer(dump_only=True)
        user_id = fields.Integer(dump_only=True)
        # nullable=False는 required=True로 대응한다.
        # String(250)은 validate로 대응한다.
        name = fields.String(required=True, validate=[validate.Length(max=250)])
        description = fields.String(required=True, validate=[validate.Length(max=500)])
    ```
   
5. `app.py`에서 `조회메서드(only 직렬화)`에, 위에서 정의한 VideoSchema를 가져와 `videos`를 serialize했던 것을 대체한다.
    ```python
    from schemas import VideoSchema
    #...
    @app.route('/tutorials', methods=['GET'])
    @jwt_required()
    def get_list():
        user_id = get_jwt_identity()
        videos = Video.query.filter(
            Video.user_id == user_id
        ).all()
    
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
        schema = VideoSchema(many=True)
        return jsonify(schema.dump(videos))
    ```
    - console에서 로그인 token을 들고 요청해서 확인해보기
    ```python
    from app import client
    id_ = 'test@gmail.com'
    password_ = '1234'
    login = client.post('login', json=dict(email='test@gmail.com', password='1234'))
    token = login.get_json()['access_token']
    auth_header = dict(Authorization=f'Bearer {token}')
    
    res = client.get('/', headers=auth_header)
    ```
   ```python
    res = client.get('/tutorials', headers=auth_header)
    res.status_code
    # 200
    res.get_json()
    # [{'description': '1234', 'id': 1, 'name': 'New Video', 'user_id': 1}, {'description': '1234', 'id': 2, 'name': 'New Video', 'user_id': 1}]
    ```

6. **Schema 객체를 만들고, dump(객체or객체list)해서 반환하는 `직렬화`과정을 `@marshal_with`데코레이터로 대체할 수 있다.**
    - before
        ```python
        @app.route('/tutorials', methods=['GET'])
        @jwt_required()
        def get_list():
            user_id = get_jwt_identity()
            videos = Video.query.filter(Video.user_id == user_id).all()
            schema = VideoSchema(many=True)
            return jsonify(schema.dump(videos))
        ```
    - after
        ```python
        @app.route('/tutorials', methods=['GET'])
        @jwt_required()
        @marshal_with(VideoSchema(many=True))
        def get_list():
            user_id = get_jwt_identity()
            videos = Video.query.filter(Video.user_id == user_id).all()
            return videos
        
        ```
    - console에서 확인
    ```python
    from app import client
    id_ = 'test@gmail.com'
    password_ = '1234'
    login = client.post('login', json=dict(email='test@gmail.com', password='1234'))
    token = login.get_json()['access_token']
    auth_header = dict(Authorization=f'Bearer {token}')
    res = client.get('/tutorials', headers=auth_header)
    res.get_json()
    # [{'description': '1234', 'id': 1, 'name': 'New Video', 'user_id': 1}, {'description': '1234', 'id': 2, 'name': 'New Video', 'user_id': 1}]
    ```
   
7. **Create route에서는 view->backend로 넘어오는 데이터들(request.json)을 `역직렬화`해야하는데, `@use_kwargs(VideoSchema)`를 이용한다**
   - id/user_id는 dump_only=True옵션이 걸려있어서, `@use_kwargs()`에 안넘어온다.
     - user_id는 token에서 get_jwt_identity()로 빼왔다.
     - id가 필요한 곳은 url_path로 넘어올 것이다.
   - @use_kwargs( schema )는 view_func`(**kwargs)`로 받아진다.
     - 내부에서 받은 데이터를 사용한다.
   ```python
    from flask_apispec import marshal_with, use_kwargs
    #...
    @app.route('/tutorials', methods=['POST'])
    @jwt_required()
    # def update_list():
    @use_kwargs(VideoSchema)
    def update_list(**kwargs):
        # new_one = Video(**request.json)
        user_id = get_jwt_identity()
        # new_one = Video(user_id=user_id, **request.json)
        new_one = Video(user_id=user_id, **kwargs)
    ```
    - 아랫부분의 직렬화부분은 `@marshal_with( schema )`로 대체하고, 직렬화 전 객체를 return한다
      - 컬렉션이 아닌 경우, VideoSchema class만 입력한다.
    ```python
    @app.route('/tutorials', methods=['POST'])
    @jwt_required()
    @use_kwargs(VideoSchema)
    @marshal_with(VideoSchema)
    def update_list(**kwargs):
        # serialized = {
        #     'id': new_one.id,
        #     'user_id': new_one.user_id,
        #     'name': new_one.name,
        #     'description': new_one.description,
        # }
        # return jsonify(serialized)
        return new_one
    ```
    - console 확인
    ```python
    from app import client
    id_ = 'test@gmail.com'
    password_ = '1234'
    login = client.post('login', json=dict(email='test@gmail.com', password='1234'))
    token = login.get_json()['access_token']
    auth_header = dict(Authorization=f'Bearer {token}')
    res = client.post('/tutorials', headers=auth_header, json={'name': 'Flask-Apispec', 'description': '직렬화/역직렬화'})
    res.status_code
    # 200
    res.get_json()
    # {'description': '직렬화/역직렬화', 'id': 3, 'name': 'Flask-Apispec', 'user_id': 1}
    
    ```
8. update route도 json데이터를 view에서 받아오니 역직렬화 + 직렬화까지 해준다
    ```python
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
    ```
9. update route에서 `객체를 못찾을 경우 message`만 반환하는 경우가 있는데, 이것도 Schema에 dump_only로 포함시켜줘야한다.
    ```python
    # app.py
    if not item:
        return {'message': 'No tutorials with this id'}, 404
       
    # schemas.py
    class VideoSchema(Schema):
        id = fields.Integer(dump_only=True)
        user_id = fields.Integer(dump_only=True)
        name = fields.String(required=True, validate=[validate.Length(max=250)])
        description = fields.String(required=True, validate=[validate.Length(max=500)])
        
        message = fields.String(dump_only=True)
    ```
10. delete route는 path로 id/token user_id  2개만 들어오고 payload가 없으므로 역직렬화는 정의안해줘도 된다.
    ```python
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
    ```
    

11. User에 대해서도 schema를 정의해준다.
    - **User model에 대해서는 `직렬화`는 `access_token만 return하므로 User객체에 대한 직렬화 schema가 할 필요가없다.`**
    - view에서 오는 payload를 받아주는 `역직렬화용 Schema`로 정의해준다
        - id가 필요없다.
    - password의 경우 read로 노출되지 않게 `load_only`를 줘야한다.
    - **relationship에 대해서는 `fields.Nested( 해당ModelSChema)` + 컬렉션이면 `many=True` 옵션을 추가해서 정의해줘야한다.**
        - 직렬화 대비? user객체는 lazy=True라서 항상 달고 있어서? 대비 로 작성해주는 듯?
    ```python
    class UserSchema(Schema):
        # User route는 id를 직렬화하지 않고 token만 내보낸다. -> 역직렬화용 -> id/fk 다 생략?!
        name = fields.String(required=True, validate=[validate.Length(max=250)])
        email = fields.String(required=True, validate=[validate.Length(max=250)])
        # password의 경우 read되면 안되므로 load_only 옵션을 줘야한다.
        password = fields.String(required=True, validate=[validate.Length(max=100)], load_only=True)
        # relationship은 Nested()로 대응하며, one-to-many일 경우, many=True옵션을 추가하고,
        # - 기본적으로 dump_only(직렬화 전용)으로 만들어준다. (차후 직렬화 대비?)
        videos = fields.Nested(VideoSchema, many=True, dump_only=True)
    ```
12. **`return {'access_token' : token}, 400`을 UserSchema말고 `AuthSchema`로 따로 정의해준다.**
    - **매핑되는 Model이 없어도, 문서화하기 위해서는 Schema와 연계되어야한다.**
    - **dict()를 반환하더라도, 그 key와 value를 Schema에 담아서 반환되도록 설정한다**
    - **success시 access_token만 반환 BUT `fail시 message만 반환`에 대비하여 message필드도 만든다.**
    - 직렬화에만 사용되므로, dump_only를 다 달고 있다.
    ```python
    class AuthSchema(Schema):
        access_token = fields.String(dump_only=True)
    
        message = fields.String(dump_only=True)
    ```
    

13. **register route에서, `역직렬화-UserSchema` / `직렬화-AuthSchema`를 달아준다.**
    - request.json 대신 역직렬화 적용하기
    ```python
    @app.route('/register', methods=['POST'])
    @use_kwargs(UserSchema)
    def register(**kwargs):
        # params = request.json
        # user = User(**params)
        user = User(**kwargs)
    ```
    - `return {'access_token': token}`을 유지하되 직렬화 AuthSchema를 거치게 하여 문서에 반영화시키기
        - 응답되는 값은 똑같이 dict -> json이지만, Schema를 거쳐서 문서화
    ```python
    @app.route('/register', methods=['POST'])
    @use_kwargs(UserSchema)
    @marshal_with(AuthSchema)
    def register(**kwargs):
    ```
    - console 확인
    ```python
    from app import client
    res = client.post('/register', json={'name': 'user3', 'email': 'test3@gmail.com', 'password': '1234'})
    res.get_json()
    # {'access_token': 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJmcmVzaCI6ZmFsc2UsImlhdCI6MTY4MDYzMzMwNSwianRpIjoiYWQwYjIyOWItY2UxOC00ZjJmLTg3Y2ItZWZmZWFmNWYyYWM5IiwidHlwZSI6ImFjY2VzcyIsInN1YiI6MiwibmJmIjoxNjgwNjMzMzA1LCJleHAiOjE2ODI3MDY5MDV9.J9JlAm3Vhn-ktxAaOFApyGo5Ot-Ok_8vPsgF045zdPs'}
    ```
    
14. **login route에서는, register에서 사용된 UserSchema의 일부만 역직렬화 되므로 `UserSchema(only=())`에 login시 필요한 payload 2개만 명시해준다.**
    - Register: name/email/password(load_only) => `역직렬화 Schema 작성 기준`
    - Login: emai/password(load_only) => `only=()를 붙여서 사용`
    ```python
    @app.route('/login', methods=['POST'])
    @use_kwargs(UserSchema(only=('email', 'password'))) # only 미작성시 register payload기준에 못미쳐서 422 뜸.
    @marshal_with(AuthSchema)
    def login(**kwargs):
        user = User.authenticate(**kwargs)
        token = user.get_token()
        return {'access_token': token}
    ```
    - **만일, Register의 역직렬화 그대로 사용한다면, login에는 name이 빠진 payload가 전달되어 `422`가 뜬다.**
        - **@use_kwargs( 제일많은payload기준으로작성된,역직렬화Schema(`only=('일부', '칼럼')`) 형식으로 사용할 것**
    ```python
    from app import client
    res = client.post('/login', json={'email': 'test3@gmail.com', 'password': '1234'})
    res.get_json()
    res.status_code
    # 200
    res.get_json()
    # {'access_token': 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJmcmVzaCI6ZmFsc2UsImlhdCI6MTY4MDYzMzc5OCwianRpIjoiMjk4YWU1NmYtNDM1Mi00NjQ4LTkxMmUtNjdkYzhjZjFmZDgzIiwidHlwZSI6ImFjY2VzcyIsInN1YiI6MiwibmJmIjoxNjgwNjMzNzk4LCJleHAiOjE2ODI3MDczOTh9.rqcjt80SgEl9TUGmTfuyAYKIM_jRYIb3Nz-TfPEt0KY'}
    ```
    

15. **역직렬화(@use_kwargs)/직렬화(@marshal_with)를 모든 route에 달았으면, 각 route들보다 더 아래에서 `docs객체에 view_func을 등록`해야 /swagger-ui에 표시된다.**
    ```python
    # app.py
    
    @app.teardown_appcontext
    def shutdown_session(exception=None):
        session.remove()
    
    # docs register view_functions
    docs.register(get_list)
    
    if __name__ == '__main__':
        app.run(host='127.0.0.1', port='5000')
    
    ```
    - `http://localhost:5000/swagger-ui/`
        ![img.png](./images/swagger_ui2.png)
    - 나머지 route view_func들도 다 등록해준다.
    - 
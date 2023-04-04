1. User 모델 만들기
   - **id대신 로그인시 exists 역할을 수행할 `email`필드는 `unique=True`로 선언한다.**
     - 만약, 실수로 생성했다면, sqlite의 경우 일단 지우고 app.py를 새로 실행해서 db를 만든다.
   - vidoes relationship을 lazy=True + backref로 간직한다(나중에 수정해야할 듯)
   ```python
    from sqlalchemy.orm import relationship
   
    class User(Base):
        __tablename__ = 'users'
        id = db.Column(db.Integer, primary_key=True)
        name = db.Column(db.String(250), nullable=False)
        email = db.Column(db.String(250), nullable=False, unique=True)
        password = db.Column(db.String(100), nullable=False)
        videos = relationship('Video', backref='user', lazy=True)
    ```
   - Video에는 User를 parent로서, fk를 가지게 한다.
   ```python
   class Video(Base):
       #...
       user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
   ```
2. `flask-jwt-extended` 패키지 설치하기
3. app.py에서 extension을 초기화해준다.
    ```python
    # extensions 
    jwt = JWTManager(app)
    ```
4. User 모델에 인스턴스메서드(각 user별)로 `get_token`메서드를 정의한다.
   - timedelta( 지정시간 )으로 만료_delta를 만들고
   - extension으로 token을 만든다. 이 때, self.id가 identity + 만료_delta가 들어간다

   ```python
   from flask_jwt_extended import create_access_token
   from datetime import timedelta
   class User(Base):
       #...
       def get_token(self, expire_time=24):
           expire_delta = timedelta(expire_time)
           token = create_access_token(
               identity=self.id,
               expires_delta=expire_delta
           )
           return token
   ```

5. 비밀번호 해시를 위해 패키지 2개 설치
   - `passlib`, `bcrypt`
   ```python
   from passlib.hash import bcrypt
   bcrypt.encrypt(p)
   bcrypt.hash(p)
   # '$2b$12$EX0XX4056OzSu1ZXraxZauFPrRWc9RMNJKMlMqrFDHr6Q/Zb9zeYK'
   ```
   
6. **User 모델에서 `password hash후 할당` 작업을 위해 `생성자 재정의`**
   - **kwargs를 받는 생성자인데, id 및 relationship 제외 password만 `hash작업 후 할당`**
   ```python
   from passlib.hash import bcrypt
   #...
   class User(Base):
       #...
       def __init__(self, **kwargs):
           self.name = kwargs.get('name')
           self.email = kwargs.get('email')
           self.password = bcrypt.hash(kwargs.get('password'))
   ```
   
7. @classmehtod로 User모델 `인증(=로그인) 메서드` 만들기
   - **`로그인에 필요한 정보(email, password)`가 인자로 올 것이다.** 
     - 인증(로그인)에 성공하면, 해당 user 데이터객체가 반환된다.
       - **`즉, user객체 조회(cls)후 -> 인증을 거친 -> 반환`까지 한번에 하는 classmethod다**
   - **`.one()`으로 조회하여 `존재하지 않을시 자동으로 에러`나게 한 상태다.**
     - 즉, exists 검증을 생략한 상태.
   - 조회후 인증이므로 -> 조회가 포함되어 cls메서드로 만든다.
   - `bcyprt`패키지는 `passlib`으로 hash암호화한 비밀번호 확인을 위함이다.
   - 비밀번호가 일치한 경우, user객체를 반환한다.
   ```python
    @classmethod
    def authenticate(cls, email, password):
        # 1. email을 unique필드로서 user객체를 one으로 찾는다.
        user = cls.query.filter(cls.email == email).one()
        # 2. user속 해쉬비밀번호 vs 들어온 비밀번호를 bcrypt패키지를 이용해서 확인하여 틀리면
        #    raise 한다.
        if not bcrypt.verify(password, user.password):
            raise Exception(f'No user with this password')
        # 3. 비밀번호가 일치하면, user개체를 반환한다
        return user
   ```
   
8. 회원가입 route 만들기 
   - exists나 password 검증들은 아직 하지 않는다.
   ```python
   @app.route('/register', methods=['POST'])
   def register():
       params = request.json
       # 1. 회원정보로 -> User모델 객체를 만들고 -> session.add해서 저장한다.
       user = User(**params)
       session.add(user)
       session.commit()
       # 2. 회원이 등록되면, 로그인 한것으로 간주하여 -> 그 때 token을 발급한다.
       token =  user.get_token()
       # 3. 응답시 'access_token' key로 내려보낸다
       return {'access_token': token}
   ```
   - console test
   ```python
   from app import client
   res = client.post('/register', json=dict(name='testuser', email='test@gmail.com', password='1234'))
   # RuntimeError: JWT_SECRET_KEY or flask SECRET_KEY must be set when using symmetric algorithm "HS256"
   ```
9. root에 `config.py` 만들어서 hash 등 인증에 필요한 `SECRET_KEY` 정의
   - config.py는 중요하지 않고 **내부 Config class안에, 모여질 상수로 정의**
   ```python
   # config.py
   class Config:
       SECRET_KEY = 
   ```
   - **secret_key를 console에서 `uuid`모듈을 이용해 생성한다.**
   ```python
   import uuid
   uuid.uuid4().hex
   '437374e9d2dc467abe0d0ab9b985c742'
   ```
   ```python
   # config.py
   class Config:
       SECRET_KEY = '437374e9d2dc467abe0d0ab9b985c742'
   ```
   
10. Config class를 import해서 `app.config.from_object( cls )`로 주입
    - 여기서 from_object는 class를 인자로 받아, class내부 상수를 config에 입력받는다.
   ```python
   from config import Config
   
   app = Flask(__name__)
   app.config.from_object(Config)
   ```
11. 다시 한번 register route console 확인
   ```python
   from app import client
   res = client.post('/register', json=dict(name='testuser', email='test@gmail.com', password='1234'))
   res.status_code
   # 200
   res.get_json()
   # {'access_token': 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJmcmVzaCI6ZmFsc2UsImlhdCI6MTY4MDU5MDMxNiwianRpIjoiMzQ5YjcyZDQtNzA3ZS00MWFiLWIzNmEtYjVlYmQ5ODBiOGQ5IiwidHlwZSI6ImFjY2VzcyIsInN1YiI6MiwibmJmIjoxNjgwNTkwMzE2LCJleHAiOjE2ODI2NjM5MTZ9.M-oEAzvJCYfZDq4W6OmUTnL0cweMeUTChyYcb1HPtjQ'}
   ```

12. login route 만들어서, 인증(로그인)메서드 성공시 token 발급하기
    ```python
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
    ```
    - console에서 register 후 login하여 만료되지 않은 token 동일한지 test
       - register시 보낸 정보에서 `name`만 제거하고 `email, password`만 보내 login
    ```python
    from app import client
    res = client.post('/register', json=dict(name='test user', email='test@gmail.com', password='1234'))
    res.get_json()
    # {'access_token': 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJmcmVzaCI6ZmFsc2UsImlhdCI6MTY4MDU5MTg5NywianRpIjoiMzM0ZTRlMzctNzgyYy00ZGEwLTk0OTgtMWE2ZjA4ZDkzNWE0IiwidHlwZSI6ImFjY2VzcyIsInN1YiI6MSwibmJmIjoxNjgwNTkxODk3LCJleHAiOjE2ODI2NjU0OTd9.y0ko3gwXxRb9ScIDnRMwOUJAzdpQp4jTQjqHWoSD7sU'}
    res = client.post('/login', json=dict(email='test@gmail.com', password='1234'))
    res.get_json()
    # {'access_token': 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJmcmVzaCI6ZmFsc2UsImlhdCI6MTY4MDU5MTkxOCwianRpIjoiMWYzNWI4ZDgtNDRmNS00NGJmLWFjZWYtMWFiMzVkNTFhNjdhIiwidHlwZSI6ImFjY2VzcyIsInN1YiI6MSwibmJmIjoxNjgwNTkxOTE4LCJleHAiOjE2ODI2NjU1MTh9.it_ssxlwN3Z5Ut8fr0qewpHYEBa7VwaRDotU_VmA1uM'}
    ```


13. **로그인이 필요한 route들에게 @login_required 대신 extension에서 제공해주는 `@jwt_required()`를 달아주면, 내부에서 알아서 access_token을 감지한다.**
   - register/login을 제외한 route들에 달아주기
   - `@jwt_required` 대신 ()를 붙인 `@jwt_required()`를 붙여야 url만 같은 다른method의 route들이 허용된다.
       ```python
       @app.route('/tutorials', methods=['GET'])
       @jwt_required()
       def get_list():
           #...
       ```
   - console에서 **`비로그인으로 @jwt_required() 접근`시, stats_code 확인**
     - **jwt extension에서 `401에러`와 `msg=`에 `인증header가 없음`을 자동으로 내려준다.** 
     ```python
     from app import client
     res = client.get('/tutorials')
     res.status_code
     # 401
     res.get_json()
     # {'msg': 'Missing Authorization Header'}
     ```

14. console에서 login날려 받은 `access_token`을 `@jwt_required()` 필요한 route 요청시 `headers=`에 추가하여 요청하기
    - 요청 headers = {} 의 dict안에 `Authorization` key / `Bearer [access_token]` value로 같이 보내면, 로그인된 상태로 간주 된다. 
    ```python
    from app import client
    
    log = client.post('login', json=dict(email='test@gmail.com', password='1234'))
    log.get_json()
    # {'access_token': 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJmcmVzaCI6ZmFsc2UsImlhdCI6MTY4MDU5Mzk2MiwianRpIjoiYmQ0YWUwMzEtMzc3ZC00NjM5LThhMGItNjk1MWE3OTQ2NTEzIiwidHlwZSI6ImFjY2VzcyIsInN1YiI6MSwibmJmIjoxNjgwNTkzOTYyLCJleHAiOjE2ODI2Njc1NjJ9.oGIU1uozNQVmy0WVBeZK9iZNtYKJJKZUWGV8yW4R8Lk'}
    token = log.get_json()['access_token']
    res = client.get('/tutorials', headers=dict(Authorization=f'Bearer {token}'))
    res.status_code
    # 200
    res.get_json()
    ```



15. 이제부터 `로그인된 user의 user_id에 딸린 video에 데이터만 C/U/D` 되어야한다.
    - **하지만, view에서는 `user_id`가 아닌 `access_token`을 headers에 넣어 보내줄 것이다.**
    - headers에 있는 `Bearer [access_token]`는 `create_access_token()`에 의해 생성될 당시 `identity=self.id`가 들어갔다.
    - **역으로 headers에 있는 `Bearer [access_token]` -> `user_id`로 변환해주는 것은 `get_jwt_identity()`메서드이다.**
    
    1. 일단 video create route부터 수정한다.
       - update할 정보들이 request.json으로 넘어오는 것은 동일하지만, 상위부모 user_id는 따로 추출되어야한다.
       ```python
        # app.py 
        from flask_jwt_extended import JWTManager, jwt_required, get_jwt_identity
        #...
        @app.route('/tutorials', methods=['POST'])
        @jwt_required()
        def update_list():
            # new_one = Video(**request.json)
            
            # @jwt_required()를 통과하면, flask의 g변수에 token정보를 집어넣어놓고 잇는데,
            # get_jwt_identity를 통해, token생성시 사용된 identity = self(user).id를 다시 반환해준다.
            user_id = get_jwt_identity() 
            new_one = Video(user_id=user_id, **request.json)
            #...
        ```
       
    2. update video route에서, 필터링 조건에 부모인 user_id가 필요되어진다.
       - **해당 Video의 id를 알고 수정할려고 해도, `부모user가 로그인한 user`여야 검색되도록 필터링에 추가한다**
       ```python
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
            #...
        ```
    3. delete video할 때도, 필터링에 Video id외에 user_id도 필터링에 포함시켜야한다
        ```python
        @app.route('/tutorials/<int:tutorial_id>', methods=['DELETE'])
        @jwt_required()
        def delete_tutorial(tutorial_id):
            # item = Video.query.filter(Video.id == tutorial_id).first()
            user_id = get_jwt_identity()
            item = Video.query.filter(
                Video.id == tutorial_id,
                Video.user_id == user_id
            ).first()
            #...
        ```
    4. 조회할 때도 특정user의 것만 조회하도록 하자.
        ```python
        @app.route('/tutorials', methods=['GET'])
        @jwt_required()
        def get_list():
            # return jsonify(tutorials)
            # videos = Video.query.all()
            user_id = get_jwt_identity()
            videos = Video.query.filter(
                Video.user_id == user_id
            ).all()
            #...
        ```
       
    5. 각각의 직렬화 응답들 대해 user_id 칼럼을 추가해준다.
        ```python
        serialized = {
            'id': item.id,
            'user_id': item.user_id,
            'name': item.name,
            'description': item.description,
        }
        ```
       
16. console에서 로그인 후 -> token들고 생성 ->token들어서 해당유저 데이터만 조회해보기
```python
from app import client
# 로그인
log = client.post('login', json=dict(email='test@gmail.com', password='1234'))
token = log.get_json()['access_token']

# 로그인 token정보 header에 달고 생성 요청
res = client.post('/tutorials', headers=dict(Authorization=f'Bearer {token}'), json=dict(name='New Video', description='1234'))
res.status_code
# 200
res.get_json()
# {'description': '1234', 'id': 2, 'name': 'New Video', 'user_id': 1}

# 로그인 token정보 header에 달고 조회 요청
res = client.get('/tutorials', headers=dict(Authorization=f'Bearer {token}'))
res.status_code
# 200
res.get_json()
# [{'description': '1234', 'id': 1, 'name': 'New Video', 'user_id': 1}, {'description': '1234', 'id': 2, 'name': 'New Video', 'user_id': 1}]

```



        


### conftest.py 참고  깃허브 정리
1. notification: https://github.com/riseryan89/notification-api/blob/master/tests/conftest.py
   - 매번 session close후 table데이터만 지우기
2. campy-server: https://github.com/CampyDB/campy-server/blob/master/tests/conftest.py
   - create_app('test') + session에 configure + tr로 데이터 제거
     - connection.begin()->close()는 1개의 tr안에서, db연결 + schema를 생성하게 하여, close()나 rollback()시 tr정보들을 db에 저장안되게 한다.
     - session은 동일engine객체로 session생성시 (bind=engine)과 connection()객체를 생성하지만,
       - **engine bind된 session VS engin.connection()이 같이 공유되지 않아, session에 engine대신, 현재connection을 bind=connection 한번 더 해준다.**  
   - flask_cache + redis 연동, init_logger
3. callcenter: https://github.com/maozhiqiang/callcenter/tree/65678718b9beadf61aa6786b43d7192f63b2cfee/flask_orm/webapp
   - create_app('test') + session에 configure + tr로 데이터 제거
   - extensions.py 따로 정리 / settings.py
4. nebula_web: https://github.com/threathunterX/nebula_query_web/blob/9c73d82f7e6bc322ea2edfd86ff62727c49d7abb/unittests/test_app.py
   - flask-sqlalchemy로서 with app.app_context()로 ext초기화작업한 상태에서 tr.close()으로 처리
   - flask-sqlalchemy의 `BaseQuery`를 `session.configure(bind=engine, query_cls=BaseQuery)`로 추가하여, .first_or_404() / .get_or_404() 처리도 되게 함

5. **flask-orm: https://github.com/CarlEkerot/flask-orm/blob/master/tests/conftest.py**
   - 어차피 engine bind된 scope_session과 현재 engine.connection()은 연결이 안되므로 
   - **test에서 직접 scope_session을 생성된 connection을 bind해서 만들어 쓰고, tr.rollback() + session.remove().**
   - flask-script로 command + shell 뿐만 아니라, serve/showurls/clean 등도 연계함.
   - controllers로 route 취급
       - `채택` -> 불합. Base.query = init속 session.query_property()등 import해오는 session객체에 기본설정을 해주는 것들이 있으므로, 새로 session생성하지말고 configure로 bind만 현재 test의 connection을 걸어준다.
   
6. **first_app: https://github.com/Beellzebub/first_app/blob/4d1ba044ad0d2e3b8c5a1fd9a439d8991c032ae2/tests/conftest.py**
   - **pytest + pytest.ini에 logger 설정 고도화**
     - **pytest.hook 구현**
   - **테스트 단위별 class황**
   - 데이터 직접제거대신, fixture를 add학 제거하는 것까지 fixture
   - **method별 client 요청 함수화**
   - **pytest.mark.parametrize사용하여 여러개 동시 테스트**

7. courier_api + fastapi 응용(response 메서드화 등): https://github.com/qvntz/courier_api/blob/bedc05d2a2d263aee139171ee8561a25fb42b3ab/tests/conftest.py#L6

### tests 모듈 및 conftest.py(Fixture) 작성

1. api폴더와 동일선상에 `tests`폴더를 `모듈`로 만든다
   - **이제 root에 있는 `db.sqlite`는 삭제하고, 앞으로 생성될 db.sqlite 완전히 `Test용 db로 취급하고, 매번 생성/삭제 될 준비를 한다`**
   
2. `conftest.py`를 만들어 fixture들을 정의한다.
   - fixture의 scope='session'(여러 test모듈(test_user.py, test_video.py)라도  한번의 pytest에서 한번만 생성한 뒤,여러 모듈에서 모두 공유하는 객체 yield)을 선택한다.
      - => app객체, app.test_client객체
   - 'module'(같은 모듈(py)내에서만, 여러개의 테스트함수라도 1번만 한번 생성하여 공유 -> 각각의 test_.py마다 독립적으로 실행되는 객체)
     - => (app context내에서의 sessio생성)
   - 'function'(개별 테스트함수마다 매번 생성되는 객체)
     - => 로그인  대상 생성 후 token발급
     - => (app context내에서의 session생성)
   - 'function', autouse=True -> 명시하지 않아도 테스트함수별로 fixture메서드가 자동 수행됨.
     - => session 생성 + (테이블생성?)  yield와서 rollback

3. test를 위한 app을 만드는데, 현재 `create_app('test)`가 존재하지 않으므로 `_app = app`으로 나타내고, fixture함수명을 `test_app`으로 작성한다
   - 전체 테스트에서 app과 connection을 1번 생성후 공유하기 위해 `session scope`로 생성한다
   ```python
   @pytest.yield_fixture(scope='session')
   def test_app():
       # _app = create_app('test)
       _app = app
   
       # 없으면 DB 및 Table 1회 생성
       Base.metadata.create_all(bind=engine)
       
       # connection을 만들고, app에 넣어서 app객체 방출 -> 끝나면 connection제거
       _app.connection = engine.connect()
       yield _app
       _app.connection.close()
   ```
   
4. client도 1회만 생성한다.
    ```python
    @pytest.fixture(scope='session')
    def client(test_app):
        return test_app.test_client()
    ```
   

5. session은 매 테스트마다 transaction으로 생성하기 위해 `function scope`로 생성하고, **session fixture를 안쓰는 경우(`Model.query`)도, `tr로 table을 비워주는 기능 or row 직접 다 삭제하는 기능`을 발동하기 위해 `autouse=True`로 작성한다**
   - **현재 app객체에 담긴 connection객체에 Transaction을 만들기 위해(session.commit해도 데이터 저장안되도록 미리 막기)위해 conn객체.begin()으로 tr을 생성한다** 
   - **`현재 Test에서 생성한 engine.connection()` VS `init에 engine바인드로 생성된 session속에 connection`이 다르기 때문에 tr이 작동안하는데, `session.configure(bind=)`에 현재 test connection을 설정해준다.**

    ```python
    @pytest.fixture(scope='function', autouse=True)
    def session(test_app):
        test_app.transaction = test_app.connection.begin()
        
        # 현재 conn객체를 init에 각종 초기화된 session객체의 conn에 bind
        db_session.configure(bind=test_app.connection)
        yield db_session
        db_session.close_all()
        ## Transaction없이 row데이터를 수동으로 직접 삭제
        # clear_data(session=db_session, except_table_names=[])
        db_session.remove()
    
        # 둘다 db에 저장안되더라.
        # test_app.transaction.close()
        test_app.transaction.rollback()
    ```
   
   - 혹시 tr을 통해 데이터를 비우는게 아니라 **직접 저장된 데이터들을 삭제하려면 아래와 같이 작성해준다.**
      - fk제약조건을 db종류(engine.name)별로 삭제 전/후에 작성하고 `table객체.delete()`로 각 테이블 row들을 모조리 삭제 한다
   ```python
   foreign_key_turn_off = {
       'mysql': 'SET FOREIGN_KEY_CHECKS=0;',
       'postgresql': 'SET CONSTRAINTS ALL DEFERRED;',
       'sqlite': 'PRAGMA foreign_keys = OFF;',
   }
   
   foreign_key_turn_on = {
       'mysql': 'SET FOREIGN_KEY_CHECKS=1;',
       'postgresql': 'SET CONSTRAINTS ALL IMMEDIATE;',
       'sqlite': 'PRAGMA foreign_keys = ON;',
   }
   
   
   def clear_data(session=None, except_table_names=None):
       # engine.name만 치면, 해당 db 문자열 이름이 나옴.
       fk_off_query = foreign_key_turn_off[engine.name]
       fk_on_query = foreign_key_turn_on[engine.name]
   
       session.execute(text(fk_off_query))
       for table in Base.metadata.sorted_tables:
           if table.name not in except_table_names:
               # exceucet 안에, metadata속 해당table.delete()만 치면 삭제 됨.
               session.execute(table.delete())
       session.execute(text(fk_on_query))
       session.commit()
    ```
    ```python
    @pytest.fixture(scope='function', autouse=True)
    def session(test_app):
        # 현재 conn객체를 init에 각종 초기화된 session객체의 conn에 bind
        db_session.configure(bind=test_app.connection)
        yield db_session
        db_session.close_all()
        db_session.remove()
    
        ## Transaction없이 row데이터를 수동으로 직접 삭제
        clear_data(session=db_session, except_table_names=[])
    ```
   
### 로그인 정보(user_headers)를 위한 User fixture 작성
0. **test_user_view.py 생성 후 작성**
1. User fixture 생성 with session in `conftest.py`
```python
@pytest.fixture(scope='function')
def user(session):
    user = User(
        name='test',
        email='test@gmail.com',
        password='1234',
    )
    session.add(user)
    session.commit()
    return user
```

2. client + User fixture를 login route에 쏴서, token 획득
    ```python
    @pytest.fixture(scope='function')
    def user_token(client, user):
        # 비밀번호는 user.password는 해쉬된 비밀번호가 들어가있다. view에서 던져줄 땐 string으로 던져야한다.
        res = client.post('/login', json={
            'email': user.email,
            'password': '1234'
        })
        return res.get_json()['access_token']
    ```
   
3. token fixture로 **로그인 정보를 담은 headers 정보 만들기**
    ```python
    @pytest.fixture(scope='function')
    def user_headers(user_token):
        return {
            'Authorization': f'Bearer {user_token}'
        }
    ```
   
4. fixture 사용해서 확인
    ```python
    # fixture 유저 확인
    def test_user_fixture(user):
        assert user.name == 'test'
    ```
   
5. fixture를 안땡겨쓰면, DB에 생성안되어있다 -> **fixture쓰지 않아 빈 DB에서 생성 Test**
   - `생성요청시 password` : 유저입력 string password 
   - `DB에 생성된 user의 password`:  hash된 상태이므로 확인 불가
   - 
    ```python
    
    # register 테스트 with client, fixture
    # -> fixture에서 등록한 'test'이라도, user_token or, user_headers를 끌어쓰지 않으면 작동안하여
    #    db에 안들어가있다.
    def test_register___fixture를_사용하지_않으면_data생성이_안되어있다(client):
        # 등록하고, 200코드인지 확인한다.
        res = client.post('/register', json={
            'name': 'test',
            'email': 'test@gmail.com',
            'password': '1234',
        })
    
        assert res.status_code == 200
    
    
    def test_register_fail___fixture를_땡겨쓰는순간_데이터는_이미_존재해있다(user, client):
        # 등록하고, 200코드인지 확인한다.
        res = client.post('/register', json={
            'name': user.name,
            'email': user.email,
            'password': '1234',
        })
    
        assert res.status_code != 200
    
    
    def test_register_fail___fixture_연계도_끌어들이는순간_중복생성으로_실패(user_token, client):
        # 등록하고, 200코드인지 확인한다.
        res = client.post('/register', json={
            'name': 'test',
            'email': 'test@gmail.com',
            'password': '1234',
        })
    
        assert res.status_code != 200
    ```
   
6. fixture를 이용해 login test
   - fixture User는 **db에 생성된 User정보라 password를 직접 못땡겨쓴다. string으로 payload를 만들어준다.**
   - login확인은 응답되는 token의 존재로 확인
    ```python
    # login 테스트
    def test_login(client, user):
        res = client.post('/login', json={
            'email': user.email,
            'password': '1234'
        })
    
        assert res.status_code == 200
        assert res.get_json().get('access_token')
    ```
   
### 특정 User에 속한 == 로그인된 상태로 == user_headers fixture사용한 체 Model(Video) test
1. test_main_views.py 생성후 작성
2. Model fixture 생성 with session **with user fixture(작성자)** in `conftest.py`
    ```python
    @pytest.fixture(scope='function')
    def video(user, session):
        video = Video(
            user_id=user.id,
            name='Test Video',
            description='test video desc'
        )
        session.add(video)
        session.commit()
    
        return video
    
    ```
   
3. **특정 유저에 대한 by `user_headers` fixture** 전체 조회 Test
    - **로그인된 상태로 조회하려면 user_headers를 json=에 가진 체로 요청하면 된다.**
       - **`user_id가 필요한 route`는 모두 `headers=user_headers`를 넣어서 요청하면, route내부에서 user_id로 변환된다.** 
    - **many 조회는 `len() == 1`로 fixture 존재유무를 테스트** 
    ```python
    def test_get_list(client, user_headers, video):
        res = client.get('/tutorials', headers=user_headers)
    
        assert res.status_code == 200
        assert len(res.get_json()) == 1
    
        # 받은 데이터의 첫번째 껏 == fixture video랑 동일한 지, dict로 1:1 비교
        assert res.get_json()[0] == {
            'id': video.id,
            'user_id': video.user_id,
            'name': video.name,
            'description': video.description,
        }
    ```
   

4. 특정유저하 생성 Test
    - **생성된 Model의 작성자정보도 확인하려면, User fixture도 써야한다** 
    ```python
    ## 생성test
    # client + 부모id by headers -> 결과확인용 부모fixture(headers에서 부모id를 바로 못뽑아서)
    # 생성: clinet + 작성자id(user_headers) + pyaload -> 자신의id는 자동배급
    def test_update_list(client, user_headers, user):
        payload = {
            'name': 'Test video',
            'description': 'test video desc',
        }
        res = client.post('tutorials', json=payload, headers=user_headers)
    
        assert res.status_code == 200
        assert res.get_json()['user_id'] == user.id
        assert res.get_json()['name'] == payload['name']
        assert res.get_json()['description'] == payload['description']
    ```

5. 특정유저의 특정 모델 수정 Test
    - 개별 대상 모델은 해당 모델의 fixture다 
    ```python
    ## update test
    # 수정: client + 작성자id(user_headers) + 대상id(fixture) + payload ->
    def test_update_tutorial(client, user_headers, video):
        payload = {
            'name': 'updated Video',
            'description': 'updated Video desc',
        }
        res = client.put(f'tutorials/{video.id}', json=payload, headers=user_headers)
    
        assert res.status_code == 200
        assert res.get_json()['name'] == payload['name']
        assert res.get_json()['description'] == payload['description']
    ```

6. 특정유저의 특정 모델 삭제 Test
    ```python
    ## delete test
    # 삭제: client + 작성자id(user_headers) + 대상id(fixture)   ->
    def test_delete_tutorial(client, user_headers, video):
    
        res = client.delete(f'tutorials/{video.id}', headers=user_headers)
        assert res.status_code == 204
    ```













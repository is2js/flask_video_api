### 예외처리 
1. 조회문 <-> return전까지를 모두 try에 올리고, **except Exception e에서는 Schema마다 포함된 message필드를 dict에서 반환하게 해준다. e는 str()로 변환해서 message의 value로 넣어준다.**
   - **except에서 message dict를 반환할 때, `상태코드도 필수`로 같이 반환해줘야 200이 안뜬다.**
    ```python
    @app.route('/tutorials', methods=['GET'])
    @jwt_required()
    @marshal_with(VideoSchema(many=True))
    def get_user_list():
        try:
            user_id = get_jwt_identity()
            videos = Video.query.filter(Video.user_id == user_id).all()
        except Exception as e:
            return {'message': str(e)}, 400
        return videos
    ```
   
2. **except에 걸리게 하려면 `try 중간에 assert None`을 추가해서 `상태코드만` test한다**
    ```python
    try:
        user_id = get_jwt_identity()
        assert None
        videos = Video.query.filter(Video.user_id == user_id).all()
    except Exception as e:
        return {'message': str(e)}, 400
    ```
    - console에서 테스트
    ```python
import models    from app import client
    id_ = 'test@gmail.com'
    password_ = '1234'
    login = client.post('login', json=dict(email='test@gmail.com', password='1234'))
    token = login.get_json()['access_token']
    auth_header = dict(Authorization=f'Bearer {token}')
    res = models.get('/tutorials', headers=auth_header)
    # C:\Users\cho_desktop\PycharmProjects\flaskProject\venv\lib\site-packages\apispec\ext\marshmallow\common.py:129: UserWarning: Multiple schemas resolved to the name User. The name has been modified. Either manually add each of the schemas with a different name or provide a custom schema_name_resolver.
    #   warnings.warn(
    res.status_code
    # 400
    res.get_json()
    # [{}]
    ```
   - **임의로 many=True 직렬화에, 예외발생시 객체 1개만 반환하면 message 내용이 아예 안내려간다.**
      - **임의로 []로를 씌운 dict message를 반환한다.**
      ```python
      def get_user_list():
           try:
               assert None
               user_id = get_jwt_identity()
               videos = Video.query.filter(Video.user_id == user_id).all()
           except Exception as e:
               # 임의로 many=True 직렬화에 대해 []로 message를 반환한다.
               return [{'message': str(e)}], 400
           return videos
      ```
   - 그외 route들도, return 객체 직전까지를 try로 묶어서 except시 message dict + 상태코드를 반환하자. 다 퉁쳐서 400 BadRequest로 처리해놓자.
   ```python
   def update_list(**kwargs):
      try:
          user_id = get_jwt_identity()
          new_one = Video(user_id=user_id, **kwargs)
          session.add(new_one)
          session.commit()
      except Exception as e:
          return {'message': str(e)}, 400
      return new_one
   ```

4. **`payload 관련 422에러`는 route 내부로직에서 잡을 수 있는 에러가 아닌 `Marshmallow`에서 발생시키므로 `@app.errorhanlder(422)`를 추가로 따로 작성해줘야한다**
   - 특정에러(422)에 대한 `@app.error_hanlder(422)`사용시 func의 인자로는 `422에 대한 exception entity`가 내려온다
      - code, name, description속성을 쓸 수 있지만, 상세에러는 `data`속성에 접근해야한다.
      - err.data에는 marshmallow가 던져주는 `headers`, `messages`, schema가 들어가있는데 이것들을 사용해서 작성해준다.
   ```python
import models    @app.errorhandler(422)
    def error_handler(err):
        # 1. 422에러를 일으킬 때의 header정보를 가져온다.
        headers = models.get('headers', None)
        
        # 2. 422에러 발생시 인자에서 'messages'(list)를 주므로 message도 가져온다.
        #   - 없을 경우 defaultt 에러message list를 반환한다.
        messages = models.get('messages', ['Invalid request'])
        # 3. header정보가 있다면, tuple 3번째 인자로 같이 반환한다
        if headers:
            return jsonify({'message' : messages}), 400, headers
        else:
            return jsonify({'message' : messages}), 400
    ```   

### loggin 적용
1. `app.py`에 route가 시작되기 전, `logger세팅 메서드 setup_logger`를 정의하고, logger객체를 전역으로 선언한다.
    ```python
    # logger
    def setup_logger():
        # 1. logger객체를 만들고, 수준을 정해준다.
        logger = logging.getLogger(__name__)
        logger.setLevel(logging.DEBUG)
    
        # 2. formatter를 작성한다
        formatter = logging.Formatter('%(asctime)s:%(name)s:%(levelname)s:%(message)s')
    
        # 3. 로그 파일을 지정 handler를 만들고, formatter를 지정해준 뒤, logger객체에 handler에 추가한다.
        file_handler = logging.FileHandler('log/api.log')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
        return logger
    
    logger = setup_logger()
    ```
    - 폴더를 자동생성해주지 않으므로, 해당 폴더가 없으면 생성후 파일명과 join해서 set해준다.
    ```python
    def setup_logger():
        # 1. logger객체를 만들고, 수준을 정해준다.
        logger = logging.getLogger(__name__)
        logger.setLevel(logging.DEBUG)
    
        # 2. formatter를 작성한다
        formatter = logging.Formatter('%(asctime)s:%(name)s:%(levelname)s:%(message)s')
    
        # 3. 로그 파일을 지정 handler를 만들고, formatter를 지정해준 뒤, logger객체에 handler에 추가한다.
        # file_handler = logging.FileHandler('log/api.log')
        # - 폴더가 없으면 FileNotFoundError가 나므로 미리 만들거나 없으면 만들어줘야한다.
        LOG_FOLDER = 'log/'
        # 나중에는 LOG_FOLDER = os.path.join(BASE_FOLDER, 'log/')
        if not os.path.exists(LOG_FOLDER):
            os.mkdir(LOG_FOLDER)
        file_handler = logging.FileHandler(os.path.join(LOG_FOLDER, 'api.log'))
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
        return logger
    ```

2. except가 발생하는 곳마다 return message하기 전에 logger객체로 `logger.warning()`을 찍어준다.
   - 확정정보 + e정보를 포함해서 작성해준다.
   - read
    ```python
    except Exception as e:
        logger.warning(
            f'user: {user_id} tutorials - read action failed with errors: {e}'
        )
        return [{'message': str(e)}], 400
    ```
   - 확정정보 user_id보다 더 아래에 `assert None`을 배치하고 console로 exception을 내서 `/log`폴더의 파일을 확인해본다.
    ```python
    try:
        user_id = get_jwt_identity()
        assert None
        videos = Video.query.filter(Video.user_id == user_id).all()
    ```
    ```python
import models    from app import client
    email_ = 'test@gmail.com'
    password_ = '1234'
    login = client.post('login', json=dict(email=email_, password=password_))
    token = login.get_json()['access_token']
    auth_header = dict(Authorization=f'Bearer {token}')
   
    res = models.get('/tutorials', headers=auth_header)
    ```
    - `log/api.log`파일
        ```
        2023-04-05 06:38:22,786:app:WARNING:user: 1 tutorials - read action failed with errors: 
        ```
    - assert None을 try에 배치하면 아무에러가 안나서 `raise Exception('test')`를 배치해서 확인해보자.
    ```python
    try:
        user_id = get_jwt_identity()
        raise Exception('test')
        videos = Video.query.filter(Video.user_id == user_id).all()
    ```
    ```python
import models    from app import client
    email_ = 'test@gmail.com'
    password_ = '1234'
    login = client.post('login', json=dict(email=email_, password=password_))
    token = login.get_json()['access_token']
    auth_header = dict(Authorization=f'Bearer {token}')
    res = models.get('/tutorials', headers=auth_header)
    ```
    ```python
    :app:WARNING:user: 1 tutorials - read action failed with errors: test
    ```
4. 이제 try 속 `raise Exception('')`을 삭제하고 read외에 c/u/d/register/login에도 로그를 찍어주자.
    ```python
    # create
    logger.warning(
                f'user: {user_id} tutorial - create action failed with errors: {e}'
            )
    
    # update/delete - 확증정보 부모user_id외 자신tutorial_id
    logger.warning(
        f'user: {user_id} tutorial:{tutorial_id} - update action failed with errors: {e}'
    )
    
    logger.warning(
        f'user: {user_id} tutorial:{tutorial_id} - delete action failed with errors: {e}'
    )
    
    # register -> xxx action이 아니라 registeration
    # - 확증정보X
    logger.warning(
        f'registration failed with errors: {e}'
    )
    
    # login -> 역직렬화 kwargs 중에 email만 확증정보로 사용(password는 readX)
    logger.warning(
        f'login with email{kwargs["email"]} failed with errors: {e}'
    )
    ```
   
5. 따로 처리한 422에러는 e정보가 아니라 err.data.messages정보를 `Invalid input params`로  찍어준다.
    ```python
    logger.warning(
        f'Invalid input params: {messages}'
    )
    ```

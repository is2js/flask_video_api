https://www.youtube.com/watch?v=lxd7qSo5vNc&list=PLWQhUNXl0LnjBIaE72hq1RkDsbWWSgeUr&index=5


1. app.py에 전역변수로 에시데이터를 만들어준다.
    ```python
    # 1. 예시데이터를 app.py에 dict로 만들기
    tutorials = \
        [
            {
                'title': 'Video #1. Intro',
                'description': 'GET, POST routes',
            },
            {
                'title': 'Video #2. More features',
                'description': 'PUT, DELETE routes',
            },
        ]
    ```
2. 전체데이터 조회(get_user_list), 데이터 추가(update_list) route를 만들어준다.
   - 데이터는 예시데이터를 jsonify()로 내려보내준다.
   - 추가할 데이터는 `request.json`으로 꺼낸다.
   ```python
   @app.route('/tutorials', methods=['GET'])
   def get_user_list():
       # 2. 예시 데이터 반환 route에서 python list는 jsonify로 jsob으로 만들어서 반환해주기
       return jsonify(tutorials)
   
   
   # 3. 추가될 데이터를 post로 받아서 예시데이터 변수에 append해주는 route개설하기
   # - request안에 json으로 오는 데이터 object 1개를 받을 예정이다.
   # - 추가후 전체데이터를 반환해주기
   @app.route('/tutorials', methods=['POST'])
   def update_list():
       new_one = request.json
       tutorials.append(new_one)
       return jsonify(tutorials)
   ```
   

3. python console에서 **url로 post, get요청을 할 수 있는 app.test_client()객체를 생성한 뒤, 요청한다.**
   ```python
   # 4. test client객체 만들어주기
   client = app.test_client()
   ```
   
4. python console에서 app객체, test_client객체를 이용해서 요청한다.
   - 응답된 jsonify 데이터는 `응답변수.get_json()`으로 받는다.
   - 응답 status는 `응답변수.status`으로 받는다.
   ```shell
   from app import app, client
   res = client.get('/tutorials')
   res.get_json()
   [{'description': 'GET, POST routes', 'title': 'Video #1. Intro'}, {'description': 'PUT, DELETE routes', 'title': 'Video #2. More features'}]
   ```
   - json데이터를 같이 보낼 경우, client.post(,json=) 인자에 dict를 넣어서 보내고
   - 백엔드에서는 `request.json`으로 받아서 쓰면 된다.
   ```shell
   from app import app, client
   res = client.get('/tutorials')
   res.get_json()
   # [{'description': 'GET, POST routes', 'title': 'Video #1. Intro'}, {'description': 'PUT, DELETE routes', 'title': 'Video #2. More features'}]
   
   
   res = client.post('/tutorials', json={'title':'Video #4', 'description': 'Unit tests'})
   res.status
   '200 OK'
   res.get_json()
   # [{'description': 'GET, POST routes', 'title': 'Video #1. Intro'}, {'description': 'PUT, DELETE routes', 'title': 'Video #2. More features'}, {'description': 'Unit tests', 'title': 'Video #4'}]
   
   
   res = client.get('/tutorials')
   res.get_json()
   # [{'description': 'GET, POST routes', 'title': 'Video #1. Intro'}, {'description': 'PUT, DELETE routes', 'title': 'Video #2. More features'}, {'description': 'Unit tests', 'title': 'Video #4'}]
   ```
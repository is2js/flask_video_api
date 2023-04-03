from flask import Flask, jsonify, request

app = Flask(__name__)

# 4. test client객체 만들어주기
client = app.test_client()
# 5. console에서 app.py에서 app객체변수, client객체변수를 import해서, client에서 .get("url")로 요청해보기
# from app import app, client
# res = client.get('/tutorials')
# res.get_json()
# [{'description': 'GET, POST routes', 'title': 'Video #1. Intro'}, {'description': 'PUT, DELETE routes', 'title': 'Video #2. More features'}]

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


@app.route('/tutorials', methods=['GET'])
def get_list():
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

# 6. console에서 client.post + json=으로 추가 요청해보기
# from app import app, client
# res = client.get('/tutorials')
# res.get_json()
# [{'description': 'GET, POST routes', 'title': 'Video #1. Intro'}, {'description': 'PUT, DELETE routes', 'title': 'Video #2. More features'}]
# res = client.post('/tutorials', json={'title':'Video #4', 'description': 'Unit tests'})
# res.status
# '200 OK'
# res.get_json()
# [{'description': 'GET, POST routes', 'title': 'Video #1. Intro'}, {'description': 'PUT, DELETE routes', 'title': 'Video #2. More features'}, {'description': 'Unit tests', 'title': 'Video #4'}]
# res = client.get('/tutorials')
# res.get_json()
# [{'description': 'GET, POST routes', 'title': 'Video #1. Intro'}, {'description': 'PUT, DELETE routes', 'title': 'Video #2. More features'}, {'description': 'Unit tests', 'title': 'Video #4'}]

@app.route('/')
def hello_world():  # put application's code here
    return 'Hello World!'


if __name__ == '__main__':
    app.run()

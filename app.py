from flask import Flask, jsonify, request

app = Flask(__name__)

# 4. test client객체 만들어주기
client = app.test_client()
# from app import app, client
# res = client.get('/tutorials')
# res.get_json()
# [{'description': 'GET, POST routes', 'title': 'Video #1. Intro'}, {'description': 'PUT, DELETE routes', 'title': 'Video #2. More features'}]
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

# 1. 예시데이터를 app.py에 dict로 만들기
# 5. update부터는 필터링할 id가 필요하여 추가
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

# 6. PUT으로 개별 tutorial item의 id를 받아 수정하는 route를 만든다.
# - 예시 list를 순회하며 필터링 한 뒤, next( , None)으로 첫번째 것만 추출한다.
# - id에 해당하는 데이터가 없을 경우, dict로 message를 만들어 반환한다. 상태코드를 tuple로서 400을 줘서 보낸다.
# - request.json으로 넘어오는 변경할 데이터를 받아서 수정한다.
# - 개별 예시데이터는 dict이므로, .update( params-dict )로 변경한다.
# - 수정된 데이터 1개는, dict이므로, 바로 return하면 된다.(list만 jsonify)
@app.route('/tutorials/<int:tutorial_id>', methods=['PUT'])
def update_tutorial(tutorial_id):
    item = next((x for x in tutorials if x['id'] == tutorial_id), None)
    params = request.json
    if not item:
        return {'message' : 'No tutorials with this id'}, 404

    item.update(params)

    return item

# 7. console로 client.put()으로 해당 route를 확인한다.
# from app import client
# res = client.put('/tutorials/2', json={'description' : 'PUT routes for editing'})
# res.status
# '200 OK'
# res.status_code
# 200
# res.get_json()
# {'description': 'PUT routes for editing', 'id': 2, 'title': 'Video #2. More features'}

# 8. 수정route(id를 qs로 사용)를 복사해서 delete route를 만든다.
# - 해당id에 대한 list의 idx를 필요로 하므로, 그 때의 idx를 enumerate()를 통해, x와 함께 가져온다.
# - 못찾을 때 0의 가능성이 있는 idx이므로 검사를 if not idx로 하면 안된다.
# - list에서 삭제는 pop(idx)를 활용한다.
# - 응답은 빈문자열 + 204(삭제성공)을 반환한다.
@app.route('/tutorials/<int:tutorial_id>', methods=['DELETE'])
def delete_tutorial(tutorial_id):
    idx, _ = next(((idx, x) for idx, x in enumerate(tutorials) if x['id'] == tutorial_id), (None, None))
    # if not idx:
    if idx is None:
        return {'message' : 'No tutorials with this id'}, 404
    tutorials.pop(idx)
    return '', 204

# 9. console에서 delete 테스트
# from app import client
# res = client.delete('/tutorials/1')
# res.status_code
# 204
# res.get_json()
# res = client.get('/tutorials')
# res.get_json()
# [{'description': 'PUT, DELETE routes', 'id': 2, 'title': 'Video #2. More features'}]

if __name__ == '__main__':
    app.run()

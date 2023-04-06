12. 예시데이터( dict_list) -> 모델.query조회(객체_list) + 빈list에 dict 변환하여 append하여 응답하도록 변경
    ```python
    @app.route('/tutorials', methods=['GET'])
    def get_user_list():
        # return jsonify(tutorials)
        videos = Video.query.all()
        serialized = []
        for video in videos:
            serialized.append({
                'id': video.id,
                'name': video.name,
                'description': video.description,
            })
        return jsonify(serialized)
    ```
    - console에서  test_client객체로 확인
    ```python
import models
    from app import client
    res = models.get('tutorials')
    res.get_json()
    # [{'description': 'SQLAlchemy apply', 'id': 1, 'name': 'Video #5'}]
    ```
    

13. create route 변경
    - 조회가 아니므로, session객체를 직접 사용한다.
    - **이젠 생성된 객체 1개만 serialize해서 반환해준다.**
    ```python
    @app.route('/tutorials', methods=['POST'])
    def update_list():
        # new_one = request.json
        # tutorials.append(new_one)
        # return jsonify(tutorials)
        new_one = Video(**request.json)
        session.add(new_one)
        session.commit()
    
        serialized = {
            'id': new_one.id,
            'name': new_one.name,
            'description': new_one.description,
        }
    
        return jsonify(serialized)
    ```
    - console에서 확인
    ```python
    from app import client
    res = client.post('tutorials', json=dict(name='test', description='test desc'))
    res.get_json()
    # {'description': 'test desc', 'id': 2, 'name': 'test'}
    ```
14. update route변경
    - **Model.query로 조회된 객체는 app.py의 session객체에 캐싱되어있어서 `data fill 이후, add없이 commit만`해주면 된다.**
    ```python
    @app.route('/tutorials/<int:tutorial_id>', methods=['PUT'])
    def update_tutorial(tutorial_id):
        # item = next((x for x in tutorials if x['id'] == tutorial_id), None)
        item = Video.query.filter(Video.id == tutorial_id).first()
        params = request.json
        if not item:
            return {'message': 'No tutorials with this id'}, 404
    
        # item.update(params)
        # return item
    
        # dictionary 업데이트 -> 객체 업데이트로 변경될 시
        # -> 1. params(payload)를 Model.query조회된 객체에 fill(setattr)을 직접 해줘야한다.
        #       => 조회하고 난 뒤, scoped_session에 캐싱되어있는 것 같다.(객체생성시는 session.add( 순수obj))
        #       print(session.identity_map.values())
        #       [<models.Video object at 0x00000242C10B5490>]
        #       => Model.query로 조회된 객체는 session에 캐싱되어있다.
        # -> 2. session으로 add없이 commit()만 해주면, 변경내역이 자동반영된다.
        for key, value in params.items():
            setattr(item, key, value)
        session.commit()
    
        serialized = {
            'id': item.id,
            'name': item.name,
            'description': item.description,
        }
        return serialized
    ```
    - console에서 확인
    ```python
    from app import client
    res = client.put('tutorials/1', json=dict(name='test111', description='test desc111'))
    res.get_json()
    {'description': 'test desc111', 'id': 1, 'name': 'test111'}
    ```
    
15. delete route 변경
    - **update와 달리 `session.delete(조회된객체)`치고 session.commit**
    ```python
    @app.route('/tutorials/<int:tutorial_id>', methods=['DELETE'])
    def delete_tutorial(tutorial_id):
        # idx, _ = next(((idx, x) for idx, x in enumerate(tutorials) if x['id'] == tutorial_id), (None, None))
        # if idx is None:
        #     return {'message': 'No tutorials with this id'}, 404
        # tutorials.pop(idx)
        # return '', 204
        item = Video.query.filter(Video.id == tutorial_id).first()
        if not item:
            return {'message': 'No tutorials with this id'}, 404
        
        session.delete(item)
        session.commit()
        return '', 204
        
    ```
    - console 확인
    ```python
    from app import client
    res = client.delete('tutorials/1')
    res.status_code
    204
    res.get_json()
    ```
    

16. test를 새로 짜주기

```python
import models
from app import client
from models import Video


def test_get_list():
    res = models.get('/tutorials')

    # 1. 상태코드 검증
    assert res.status_code == 200
    # 2. 응답받은 전체데이터 갯수 VS DB조회시 전체데이터 갯수
    assert len(res.get_json()) == len(Video.query.all())
    # 3. 첫번째 응답 데이터의 id 확인?!
    #  => my) 맨 마지막 데이터 확인으로 변경
    assert res.get_json()[-1]['id'] == Video.query.all()[-1].id


def test_update_list():
    ### 데이터 생성
    # 1. 생성용 payload(json) 생성 (id 제외)
    data = {
        'name': 'Unit Tests',
        'description': 'Pytest tutorial'
    }

    res = client.post('/tutorials', json=data)

    # 2. 상태 코드
    assert res.status_code == 200

    # 3. 생성 요청시 보낸 data(unique필드) <-> 생성된 데이터의 응답객체의 필드 비교
    # - 요청payload(data)는 id가 없으므로 id말고 unique필드 비교
    assert res.get_json()['name'] == data['name']


def test_update_tutorial():
    # 1. 업데이트할  대상 + 필드 및 값
    # => my) 기존에 있는 데이터로 하기 위해, 맨 마지막 데이터를 조회하고 변경한다
    last_video = Video.query.all()[-1]
    # res = client.put('/tutorials/2', json={'name': 'UPDATE'})
    res = client.put(f'/tutorials/{last_video.id}', json={'name': 'UPDATE last video'})

    # 2. 상태코드
    assert res.status_code == 200
    # 3. 업데이트 대상의 필드 조회 == 업데이트 값
    assert models.get(last_video.id).name == 'UPDATE last video'


def test_delete_tutorial():
    # 1. 삭제할 대상id 지정
    # => 존재해야하므로 맨 마지막 것을 조회해서 삭제 타겟으로 둔다.
    # res = client.delete('/tutorials/2')
    last_video = Video.query.all()[-1]

    res = client.delete(f'/tutorials/{last_video.id}')

    # 2. 상태코드(삭제성공: 204)
    assert res.status_code == 204
    # 3. 대상id로 조회시 is None
    assert models.get(last_video.id) is None

```
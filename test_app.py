import models
from app import client
from models import Video


# def test_get_list():
#     ### 예시데이터 전체 조회
#     res = client.get('/tutorials')
# 
#     # 1. 상태코드 검증
#     assert res.status_code == 200
#     # 2. list의 갯수, 및 첫번째 item의 id 검사
#     assert len(res.get_json()) == 2
#     assert res.get_json()[0]['id'] == 1

def test_get_list():
    res = models.get('/tutorials')

    # 1. 상태코드 검증
    assert res.status_code == 200
    # 2. 응답받은 전체데이터 갯수 VS DB조회시 전체데이터 갯수
    assert len(res.get_json()) == len(Video.query.all())
    # 3. 첫번째 응답 데이터의 id 확인?!
    #  => my) 맨 마지막 데이터 확인으로 변경
    assert res.get_json()[-1]['id'] == Video.query.all()[-1].id


# def test_update_list():
#     ### 예시데이터 생성
#     # 1. 생성용 payload(json) 생성
#     data = {
#         'id': 3,
#         'title': 'Unit Tests',
#         'description': 'Pytest tutorial'
#     }
#     res = client.post('/tutorials', json=data)
#
#     # 2. 상태 코드
#     assert res.status_code == 200
#
#     # 3. (생성후 전체데이터 list반환하므로) 갯수 검증
#     assert len(res.get_json()) == 3
#     # 4. 생성 요청시 보낸 data(unique필드) <-> 응답된 것 중 추가된 제일 마지막data 비교
#     # - 요청payload(data)는 id가 없으므로 id말고 unique필드 비교
#     assert res.get_json()[-1]['title'] == data['title']

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


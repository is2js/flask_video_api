from app import client


def test_get_list():
    ### 전체 조회
    res = client.get('/tutorials')

    # 1. 상태코드 검증
    assert res.status_code == 200
    # 2. list의 갯수, 및 첫번째 item의 id 검사
    assert len(res.get_json()) == 2
    assert res.get_json()[0]['id'] == 1


def test_update_list():

    ### 생성
    # 1. 생성용 payload(json) 생성
    data = {
        'id': 3,
        'title': 'Unit Tests',
        'description': 'Pytest tutorial'
    }
    res = client.post('/tutorials', json=data)

    # 2. 상태 코드
    assert res.status_code == 200

    # 3. (생성후 전체데이터 list반환하므로) 갯수 검증
    assert len(res.get_json()) == 3
    # 4. 생성 요청시 보낸 data(unique필드) <-> 응답된 것 중 추가된 제일 마지막data 비교
    # - 요청payload(data)는 id가 없으므로 id말고 unique필드 비교
    assert res.get_json()[-1]['title'] == data['title']

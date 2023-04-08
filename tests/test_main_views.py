# fixture user에 의해 생성된 video들을 조회하기 위해
# fixture user_headers를 쓴다.
# + 그 특정video를 확인하기 위해, fixture video도 받는다.
# client + 작성자id (user_headers) -> 결과확인용 자신fixture
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


## delete test
# 삭제: client + 작성자id(user_headers) + 대상id(fixture)   ->
def test_delete_tutorial(client, user_headers, video):

    res = client.delete(f'tutorials/{video.id}', headers=user_headers)
    assert res.status_code == 204


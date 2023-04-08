import pytest


# fixture 유저 확인
def test_user_fixture(user):
    assert user.name == 'test'


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


# login 테스트
def test_login(client, user):
    res = client.post('/login', json={
        'email': user.email,
        'password': '1234'
    })

    assert res.status_code == 200
    assert res.get_json().get('access_token')

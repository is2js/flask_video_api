10. 패키지에서 `pytest`르 설치 한 뒤, root에  `tests.py`를 만들고
    - `def test_xxxx():`메서드를 만들어 내부에 `assert`를 넣어서 검증한다.
    ```python
    def test_simple():
        my_list = [1, 2, 3, 4, 5]
    
        assert 3 in my_list
    ```
    - 이후 **terminal에서 `pytest ./tests.py`로 테스트를 실행한다**
    ```shell
    pytest ./tests.py
    ```
    - **`pycharm`에서는 `tests.py`내부에서 실행시키면 된다.**

11. 각 route함수에서 `alt+insert`로 테스트를 만들어서 사용한다.

12. 전체조회/생성에 대한 test
    - 전체조회시 list의 길이 + 첫번째 item의 id확인
    - 생성요청시 전체list반환되어, 전체길이(기존+1) + 마지막데이터의 unique필드 비교
    ```python
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
    ```
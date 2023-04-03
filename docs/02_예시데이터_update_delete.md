5. 예시 데이터 update부터는 id가 필요하다. list의 각 아이템에 id 배정
   ```python
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
   ```
6. PUT으로 개별 tutorial item의 id를 받아 수정하는 route를 만든다.
   - 예시 list를 순회하며 필터링 한 뒤, next( , None)으로 첫번째 것만 추출한다.
   - id에 해당하는 데이터가 없을 경우, dict로 message를 만들어 반환한다. 상태코드를 tuple로서 400을 줘서 보낸다.
   - request.json으로 넘어오는 변경할 데이터를 받아서 수정한다.
   - 개별 예시데이터는 dict이므로, .update( params-dict )로 변경한다.
   - 수정된 데이터 1개는, dict이므로, 바로 return하면 된다.(list만 jsonify)
   ```python
   @app.route('/tutorials/<int:tutorial_id>', methods=['PUT'])
   def update_tutorial(tutorial_id):
       item = next((x for x in tutorials if x['id'] == tutorial_id), None)
       params = request.json
       if not item:
           return {'message' : 'No tutorials with this id'}, 404

       item.update(params)

       return item
   ```
   
7. console로 client.put()으로 해당 route를 확인한다.
   ```shell
   from app import client
   res = client.put('/tutorials/2', json={'description' : 'PUT routes for editing'})
   res.status
   # '200 OK'
   res.status_code
   # 200
   res.get_json()
   # {'description': 'PUT routes for editing', 'id': 2, 'title': 'Video #2. More features'}
   ```

8. 수정route(id를 qs로 사용)를 복사해서 delete route를 만든다.
   - 해당id에 대한 list의 idx를 필요로 하므로, 그 때의 idx를 enumerate()를 통해, x와 함께 가져온다.
   - 못찾을 때 0의 가능성이 있는 idx이므로 검사를 if not idx로 하면 안된다.
   - list에서 삭제는 pop(idx)를 활용한다.
   - 응답은 빈문자열 + 204(삭제성공)을 반환한다.
   ```python

   @app.route('/tutorials/<int:tutorial_id>', methods=['DELETE'])
   def delete_tutorial(tutorial_id):
       idx, _ = next(((idx, x) for idx, x in enumerate(tutorials) if x['id'] == tutorial_id), (None, None))
       # if not idx:
       if idx is None:
           return {'message' : 'No tutorials with this id'}, 404
       tutorials.pop(idx)
       return '', 204
   ```
   
9. console에서 delete 테스트
   ```shell
   from app import client
   res = client.delete('/tutorials/1')
   res.status_code
   #204
   res.get_json()
   
   
   res = client.get('/tutorials')
   res.get_json()
   #[{'description': 'PUT, DELETE routes', 'id': 2, 'title': 'Video #2. More features'}]
   ```

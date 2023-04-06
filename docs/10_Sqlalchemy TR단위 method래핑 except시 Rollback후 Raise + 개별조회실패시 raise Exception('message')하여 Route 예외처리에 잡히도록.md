1. **조회 transaction단위 -> Model내 @classmethod로 래핑하고, 예외발생시 raise하면, 외부 try/except에서 잡힌다.**
   - before
       ```python
       try:
           user_id = get_jwt_identity()
           videos = Video.query.filter(Video.user_id == user_id).all()
       ```
   - after
   1. 메서드 추출하여 외부인자는 받아들이게 한다
       ```python
       try:
           user_id = get_jwt_identity()
           videos = get_by_user_id(user_id)
            
       def get_user_list(user_id):
           return Video.query.filter(Video.user_id == user_id).all()
       ```
   2. 추출한 메서드를 Video(해당 모델) 내부 메서드로 옮기되, Video가 내부에 사용되면 @classmethod로 바꾸고, cls인자로 바꿔준다.
       ```python
import video_api.main.views       # app.py
       try:
           user_id = get_jwt_identity()
           videos = video_api.main.views.get_user_list(user_id=user_id)
       ```
       ```python
       # models.py
       @classmethod
       def get_user_list(cls, user_id):
           return cls.query.filter(cls.user_id == user_id).all()
       ```

   3. **하나의 transaction단위로서 `try/except`를 걸고, `except예외발생시 rollback후 raise`하여 session은 롤백하고, 바깥에서 예외가 잡히도록 한다**
      - **바로 `return 쿼리.결과()`가 아니라, `쿼리결과 변수로 추출 -> ta session처리 in try` -> `결과물 return`이다.**
      - session은 app.py에서 만든 scopred_session을 import해온 것인데, Model.query에도 동시에 사용되므로, 서로 일치하는 session이다.
      ```python
      # models.py
      @classmethod
      def get_user_list(cls, user_id):
        try:
            # 1. 바로 return 쿼리.결과()가 아니라 => 변수로 추출 + TA session처리 in try만 하고, 성공시 raise안걸리고 return되게 한다
            videos = cls.query.filter(cls.user_id == user_id).all()
            session.close()
        except Exception:
            # 2. 모델.query의 조회session과 일치하는 scoped_session을 rollback후 바깥에서 잡히도록 raise한다
            session.rollback()
            raise
        return videos
      ```

2. **create TR단위는 model객체 생성 이후 -> `session.add/session.commit`까지다**
   - cls가 아닌 객체단위에서 호출하는 instance method로 래핑한다
   - before
      ```python
       try:
           user_id = get_jwt_identity()
           new_one = Video(user_id=user_id, **kwargs)
           session.add(new_one)
           session.commit()
      ```
   - after 
      ```python
       try:
           user_id = get_jwt_identity()
           new_one = Video(user_id=user_id, **kwargs)
           new_one.save()
      ```
      ```python
       def save(self):
           try:
               session.add(self)
               session.commit()
           except Exception:
               session.rollback()
               raise
      ```
     
3. **update TR단위는 `개별조회(cls)` + `확인로직` + `setattr + commit`인데, 중간에 route에서 확인로직이 있으므로 `조회+확인로직(alive session)` + `update`를 개별로 메서드래핑`해준다.**
   - 전체조회는 list로 반환되어 데이터없어도 `[]`빈 list반환여 .first()의 None반환을 확인할 필요가 없었다
   - **개별조회시 `if not item 확인로직에 걸린`다면 return message+code대신 `raise Exception('message text')`를 발생시켜 `밖 route의 예외처리에서 해당 message가 반환`되도록 설계한다.**
   - **update로직은 `개별조회시 session close를 하지 않고 session에 담긴상태`에서 이어가므로 `setattr이후 commit`만 때리면 되게 구성한다**
   - before
   ```python
    try:
        user_id = get_jwt_identity()
        # 개별조회 + 확인로직
        item = Video.query.filter(
            Video.id == tutorial_id,
            Video.user_id == user_id
        ).first()
        if not item:
            return {'message': 'No tutorials with this id'}, 404
        
        # update 로직
        for key, value in kwargs.items():
            setattr(item, key, value)
        session.commit()
   ```
   1. 개별조회 + 확인로직 래핑
   ```python
   # 개별조회 + 확인로직
   item = Video.get(tutorial_id, user_id)
   ```
   ```python
    @classmethod
    def get(cls, tutorial_id, user_id):
        item = cls.query.filter(
            cls.id == tutorial_id,
            cls.user_id == user_id
        ).first()
        if not item:
            return {'message': 'No tutorials with this id'}, 404
        return item
   ```   
   ```python
    @classmethod
    def get(cls, tutorial_id, user_id):
        video = cls.query.filter(
            cls.id == tutorial_id,
            cls.user_id == user_id
        ).first()
        if not video:
            # return {'message': 'No tutorials with this id'}, 404
            raise Exception('No tutorials with this id')
        return video
    ```
    ```python
    @classmethod
    def get(cls, tutorial_id, user_id):
        try:
            video = cls.query.filter(
                cls.id == tutorial_id,
                cls.user_id == user_id
            ).first()
            if not video:
                # return {'message': 'No tutorials with this id'}, 404
                raise Exception('No tutorials with this id')

            # 개별이후 update가 이루어질 것이라서, TR session을 닫는 것을 보류한다.
        except Exception:
            session.rollback()
            raise
        return video
    ```
    2. update로직(객체 alive session 상태)
        - **조심해야할 것은, 메서드 추출하더라도 메서드엔 `dict인 kwargs`대신 `키워드입력 **kwargs`로 받아주고, 최종 update메서드 내부에선 kwagrs를 dict로 활용하도록 하자**
    ```python
    # update로직
        update(item, kwargs)
    ```
    ```python
    def update(item, kwargs):
        for key, value in kwargs.items():
            setattr(item, key, value)
        session.commit()
    ```
    ```python
    # update로직 -> **kwargs를 인자에 유지하면, [키워드입력]이 된다
    item.update(**kwargs) 
    
    # models.py
    def update(item, **kwargs):
        for key, value in kwargs.items():
            setattr(item, key, value)
        session.commit()
    ```
    ```python
    def update(self, **kwargs):
        try:
            for key, value in kwargs.items():
                setattr(self, key, value)
            session.commit()
        except Exception:
            session.rollback()
            raise
    ```
4. detelte는 update시 개별조회+확인 method get() 그대로 사용하고 alive상태의 객체를 delete하는 것만 작성해준다.
   ```python
    def delete(self):
        try:
            session.delete(self)
            session.commit()
        except Exception:
            session.rollback()
            raise
   ```   
   

5. login말고 Register만 .save()로 래핑할 필요가 있다.
   - 왠지, BaseModel에서 공통적으로 정의해줘야할 듯?
   ```python
   def register(**kwargs):
       try:
           user = User(**kwargs)
           user.save()
           token = user.get_token()
   ```
   ```python
    def save(self):
        try:
            session.add(self)
            session.commit()
        except Exception:
            session.rollback()
            raise
   ```
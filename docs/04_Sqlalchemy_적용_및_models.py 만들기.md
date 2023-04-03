1. sqlalchemy 설치
2. 필요모듈 app.py에 import
   - sqlalchemy를 `db`로 app.py에 1번 import해놓고, **개별 model들의 column정의시 app.py의 db(sqlalchemy)로 `db.Column`으로 정의하게 한다.**
    ```python
    import sqlalchemy as db
    from sqlalchemy.orm import sessionmaker, scoped_session
    from sqlalchemy import create_engine
    from sqlalchemy.ext.declarative import declarative_base
    ```
   
3. db_url을 통한 engine 생성
    ```python
    engine = create_engine('sqlite:///db.sqlite')
    ```
4. bind=engine + commit/flush여부를 통해 `sessionmaker()`를 만들고, `scoped_session()`을 씌워서 session객체를 만들어 할당
    ```python
    session = scoped_session(sessionmaker(
        autocommit=False, autoflush=False, bind=engine
    ))
    ```
   
5. app종료시, session.remove()해주는 teardown_appcontext를 route들 맨 끝에 작성해주기
    ```python
    @app.teardown_appcontext
    def shutdown_session(exception=None):
        session.remove()
    
    if __name__ == '__main__':
        app.run()
    
    ```
   
6. **`app.py`에 Base객체 만들고, `Base.query`에 `session.query_property()`를 배정해줘서, Model.query 사용가능하게 하기**
   - **app.py의 `session = `객체와 별개로, `개별model 조회용 session`이라고 생각한다.**
     - 조회에서는 `Model.query`
     - 그외 CUD시에는 `session.add( 조회된 객체)` 등이 필요하다.
   ```python
   Base = declarative_base()
   Base.query = session.query_property()
   ```
   
7. root에 `models.py`를 만들고 `db(sqlalchemy in app.py)`, `Base`, `session`을 import한다.
   - model의 column 정의시 session이 사용되진 않는다.
   ```python
   from app import db, session, Base
   
   class Video(Base):
       __tablename__ = 'videos'
   
       id = db.Column(db.Integer, primary_key=True)
       name = db.Column(db.String(250), nullable=False)
       description = db.Column(db.String(500), nullable=False)
   ```
   
8. `app.py`에서 model을 route에서 써야하는데, model은 app.py의 객체들을 import하고 있으니
   - import한 db, session, Base보다 더 아래에서 import한다 
   - **`Base.metadata.create_all(bind=engine)`을 때려서 db_url에 테이블을 생성해야하는데, `모든 model객체가 메모리에 import된 상태`여야한다.**
   ```python
   # app.py
   
   Base = declarative_base()
   Base.query = session.query_property()
   # models.py가 import한 Base보다 더 밑에서 import된다.
   # create_all 전에 메모리에 models들이 떠있어야한다.
   from models import *
   Base.metadata.create_all(bind=engine)
   ```
   
9. 이제 app.py를 실행하면, 자동으로 없으면 db까지 + table이 생성된다.
   ```shell
   python app.py
   ```
   
10. **db, models.py가 생성된 상태면, `console에서 Model 조회 가능`**
   ```shell
   python
   ```
   ```python
   from models import Video
   v = Video.query.all()  
   v
   # []
   ```

11. 데이터를 생성하려면, Model()객체를 만들고 `from app import session`을 가져와서 수행한다.
    - Model.query에 달린 `session.query(Model)`은 only 조회용이다.
   ```shell
   python
   ```
   ```python
   from models import Video
   v1 = Video(name='Video #5', description='SQLAlchemy apply')
   
   from app import session
   session.add(v1)
   session.commit()
   v = Video.query.all()                                       
   v
   #[<models.Video object at 0x00000207A4F93FA0>]
   ```
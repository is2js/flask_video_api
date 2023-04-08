import pytest
from sqlalchemy import text
from sqlalchemy.orm import sessionmaker, scoped_session

# 0. 만약, tests모듈이 최상위폴더가 아니라면, 등산했다가 video_api모듈을 불러야하므로
# import sys
# sys.path.append('..')
# 로 import 직전에 미리 등산해놓는다.
# 1. api사위모듈의 init속 app객체와 Base, engine객체 가져온다
from video_api import app, Base, engine, session as db_session
from video_api.models import User, Video


# https://github.com/riseryan89/notification-api/blob/master/tests/conftest.py
# @dataclass
# class TestConfig(Config):
#     DB_URL: str = "mysql+pymysql://travis@localhost/notification_test?charset=utf8mb4"
#     TRUSTED_HOSTS = ["*"]
#     ALLOW_SITE = ["*"]
#     TEST_MODE: bool = True
# from app.main import create_app
# from app.database.conn import db, Base
# @pytest.fixture(scope="session")
# def app():
#     os.environ["API_ENV"] = "test"
#     return create_app()

# https://github.com/CampyDB/campy-server/blob/master/tests/conftest.py
# class TestingConfig(Config):
#     TESTING = True
#     DATABASE_URI = 'postgresql://campy:campy_password@localhost:5432/campy_test_db'
# from app import Base, create_app, session
# @pytest.yield_fixture(scope='session')
# def app():
#     _app = create_app('testing')
#     _app.testing = True
#     Base.metadata.drop_all(bind=_app.engine)
#     Base.metadata.create_all(bind=_app.engine)
#     _app.connection = _app.engine.connect()
#
#     session.configure(bind=_app.connection)
#
#     yield _app
#
#     _app.connection.close()
#     Base.metadata.drop_all(bind=_app.engine)

# https://github.com/maozhiqiang/callcenter/blob/65678718b9beadf61aa6786b43d7192f63b2cfee/flask_orm/tests/conftest.py
# class TestConfig(Config):
#     DEBUG = True
#     TESTING = True
#     LOGIN_DISABLED = False
#
#     SQLALCHEMY_DATABASE_URI = 'sqlite://'
#     SQLALCHEMY_TRACK_MODIFICATIONS = False
#     SQLALCHEMY_ECHO = True

# from flask_orm.webapp import db, create_app
# from flask_orm.webapp.settings import TestConfig

# @pytest.yield_fixture(scope="session")
# def app():
#     _app = create_app(TestConfig)
#     db.app = _app
#     db.create_all()
#
#     _app.connection = db.engine.connect()
#
#     yield _app
#
#     _app.connection.close()
#     db.drop_all()


# https://github.com/threathunterX/nebula_query_web/blob/9c73d82f7e6bc322ea2edfd86ff62727c49d7abb/unittests/conftest.py#L3
# from test_app import create_app, DbSession
#
# import pytest
# from sqlalchemy.ext.declarative import declarative_base
#
# Base = declarative_base()
# TESTDB = 'test_project.db'
# TESTNebulaDB = 'test_nebula.db'
# TESTDB_PATH = "/tmp/{}".format(TESTDB)
# TEST_DATABASE_URI = 'sqlite:///' + TESTDB_PATH
# TEST_Nebula_DATABASE_URI = 'sqlite:///' + TESTDB_PATH
# TestConfig = {
#     'TESTING': True,
#     'SQLALCHEMY_DATABASE_URI': TEST_DATABASE_URI,
#     'SQLALCHEMY_BINDS' : {"nebula":TEST_Nebula_DATABASE_URI}
# }
#
# @pytest.yield_fixture(scope="session")
# def app():
#     """
#     Creates a new Flask application for a test duration.
#     Uses application factory `create_app`.
#     """
#     _app = create_app("testingsession", config_object=TestConfig)
#
#     # Base is declarative_base()
#     Base.metadata.create_all(bind=_app.engine)
#     _app.connection = _app.engine.connect()
#
#     # No idea why, but between this app() fixture and session()
#     # fixture there is being created a new session object
#     # somewhere.  And in my tests I found out that in order to
#     # have transactions working properly, I need to have all these
#     # scoped sessions configured to use current connection.
#     DbSession.configure(bind=_app.connection)
#
#     yield _app
#
#     # the code after yield statement works as a teardown
#     _app.connection.close()
#     Base.metadata.drop_all(bind=_app.engine)

# https://github.com/CarlEkerot/flask-orm/blob/698f9b98a20b5944e97020b15d8d7bc887dd4d76/tests/conftest.py
# from webapp import db, create_app
# from webapp.settings import TestConfig
#
#
# @pytest.yield_fixture(scope="session")
# def app():
#     _app = create_app(TestConfig)
#     db.app = _app
#     db.create_all()
#
#     _app.connection = db.engine.connect()
#
#     yield _app
#
#     _app.connection.close()
#     db.drop_all()


# 2. fixture의 scope='session'(여러 test모듈(test_user.py, test_video.py)라도  한번의 pytest에서 한번만 생성한 뒤,여러 모듈에서 모두 공유하는 객체 yield)을 선택한다.
#                    => app객체, app.test_client객체
#                   'module'(같은 모듈(py)내에서만, 여러개의 테스트함수라도 1번만 한번 생성하여 공유 -> 각각의 test_.py마다 독립적으로 실행되는 객체)
#                    => (app context내에서의 sessio생성)
#                   'function'(개별 테스트함수마다 매번 생성되는 객체)
#                    => 로그인  대상 생성 후 token발급
#                    => (app context내에서의 session생성)
#                   'function', autouse=True -> 명시하지 않아도 테스트함수별로 fixture메서드가 자동 수행됨.
#                    => session 생성 + (테이블생성?)  yield와서 rollback
# 3. app객체에 대한 fixture를 먼저 작성한다.
# -
@pytest.yield_fixture(scope='session')
def test_app():
    # _app = create_app('test)
    _app = app

    # 없으면 DB 및 Table 1회 생성
    Base.metadata.create_all(bind=engine)

    # connection을 만들고, app에 넣어서 app객체 방출 -> 끝나면 connection제거
    _app.connection = engine.connect()
    yield _app
    _app.connection.close()


# 4. user login 요청을 위한 client도 fixture -> 전체 테스트동안 공유되므로 session
@pytest.fixture(scope='session')
def client(test_app):
    return test_app.test_client()


# session은 매 테스트마다 transaction으로 생성하기 위해 `function scope`로 생성하고, **session fixture를 안쓰는 경우(`Model.query`)도, `tr로 table을 비워주는 기능 or row 직접 다 삭제하는 기능`을 발동하기 위해 `autouse=True`로 작성한다**
# **현재 app객체에 담긴 connection객체에 Transaction을 만들기 위해(session.commit해도 데이터 저장안되도록 미리 막기)위해 conn객체.begin()으로 tr을 생성한다**
# **`현재 Test에서 생성한 engine.connection()` VS `init에 engine바인드로 생성된 session속에 connection`이 다르기 때문에 tr이 작동안하는데, `session.configure(bind=)`에 현재 test connection을 설정해준다.**
@pytest.fixture(scope='function', autouse=True)
def session(test_app):
    test_app.transaction = test_app.connection.begin()

    # 현재 conn객체를 init에 각종 초기화된 session객체의 conn에 bind
    db_session.configure(bind=test_app.connection)
    yield db_session
    db_session.close_all()
    ## Transaction없이 row데이터를 수동으로 직접 삭제
    # clear_data(session=db_session, except_table_names=[])
    db_session.remove()


    # 둘다 db에 저장안되더라.
    # test_app.transaction.close()
    test_app.transaction.rollback()

foreign_key_turn_off = {
    'mysql': 'SET FOREIGN_KEY_CHECKS=0;',
    'postgresql': 'SET CONSTRAINTS ALL DEFERRED;',
    'sqlite': 'PRAGMA foreign_keys = OFF;',
}

foreign_key_turn_on = {
    'mysql': 'SET FOREIGN_KEY_CHECKS=1;',
    'postgresql': 'SET CONSTRAINTS ALL IMMEDIATE;',
    'sqlite': 'PRAGMA foreign_keys = ON;',
}


def clear_data(session=None, except_table_names=None):
    # engine.name만 치면, 해당 db 문자열 이름이 나옴.
    fk_off_query = foreign_key_turn_off[engine.name]
    fk_on_query = foreign_key_turn_on[engine.name]

    session.execute(text(fk_off_query))
    for table in Base.metadata.sorted_tables:
        if table.name not in except_table_names:
            # exceucet 안에, metadata속 해당table.delete()만 치면 삭제 됨.
            session.execute(table.delete())
    session.execute(text(fk_on_query))
    session.commit()


# 3. session + transaction이 완성되면, 매번 테스트에 필요한 User객체를 만들어준다.
# -> session scope로 만들면, 테스트마다 로그인 독립성이 떨어질 듯.
@pytest.fixture(scope='function')
def user(session):
    user = User(
        name='test',
        email='test@gmail.com',
        password='1234',
    )
    session.add(user)
    session.commit()
    return user


# 5. user객체 + client -> login route로 요청한 뒤, res.get_json()에서 토큰 받기
@pytest.fixture(scope='function')
def user_token(client, user):
    # 비밀번호는 user.password는 해쉬된 비밀번호가 들어가있다. view에서 던져줄 땐 string으로 던져야한다.
    res = client.post('/login', json={
        'email': user.email,
        'password': '1234'
    })
    return res.get_json()['access_token']


@pytest.fixture(scope='function')
def user_headers(user_token):
    return {
        'Authorization': f'Bearer {user_token}'
    }


## 조회 test를 위해 데이터 생성 with 부모fixture
# 특정 user fixture(로그인으로 해당user의 user_headers)에 대한 video fixture 생성
# -> 조회시 user_headers를 받아서, id를 사용할 예정
@pytest.fixture(scope='function')
def video(user, session):
    video = Video(
        user_id=user.id,
        name='Test Video',
        description='test video desc'
    )
    session.add(video)
    session.commit()

    return video

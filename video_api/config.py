import os


class Config:
    # [.env ]-> docker-compose의 [environments] 변수들 export -> python에선 [os.getenv]
    # => docker-compose가 없이도 실행되려면 or로 default값 넣어놓기
    # => 나중에는 load_dotenv로 [.env] -> docker-compose없이 바로 python에서 [os.getenv]
    SECRET_KEY = os.getenv('SECRET_KEY') or 'secret_key'
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URI') or 'sqlite:///db.sqlite'

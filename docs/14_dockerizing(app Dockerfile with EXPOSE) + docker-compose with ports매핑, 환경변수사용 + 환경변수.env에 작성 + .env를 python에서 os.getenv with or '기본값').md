- 도커 명령어 참고
  1. [전체 명령어 참고](https://devvvyang.tistory.com/59#:~:text=RUN%20%EB%AA%85%EB%A0%B9%EC%96%B4%EB%8A%94%20%EC%9D%B4%EB%AF%B8%EC%A7%80%EB%A5%BC,%EB%A5%BC%20%EC%9E%91%EC%84%B1%ED%95%98%EB%8A%94%20%EB%B6%80%EB%B6%84%EC%9D%B4%EB%8B%A4.)
  2. [[Docker] RUN, CMD, ENTRYPOINT 차이점](https://seokhyun2.tistory.com/61)
  3. [비슷한 명령어 구분해서](https://miiingo.tistory.com/90)
  4. [expose vs pose 등 배포관련 더 자세히](https://miiingo.tistory.com/92)

### app container를 만드는 Dockerfile
1. **docker내부에서 CMD(덮어쓰여질수 있는 container실행시 명령어)에 사용될 `gunicorn`부터 설치**
   ```shell
   # window에서 실행 안됨.
   pip instlal gunicorn
   ```
2. **docker내부에서 패키지 설치를 위해 `pip freeze > requirements.txt`부터**
   ```shell
   pip freeze > requirements.txt
   ```
3. root에 `Dockerfile` 생성
   1. 기본 image에 python image를 `FROM python:버.전`으로 함께 지정
   2. 현재(root)의 모든 정보(`.`)를 -> container의 `/app`폴더로 복사(`COPY`)
      1. COPY: 호스트->container로 복사만 
      2. ADD: 디렉토리 생성 및 파일복사 + url 복사 + 압축 풀기 등
   3. 앞으로 작업할 기준 디렉토리를 파일을 이동시킨 `/app`로 변환(`WORKDIR`)
   4. app폴더로 이동한 상태로, `requirements.txt`기준으로 `pip install -r`를 통해 패키지 설치 명령어(`RUN`) 실행
      1. RUN: image빌드시 반드시 실행되어야할 명령어 ex> 기본image에 추가될 패키지 설치 명령어
      2. CMD: container 생성시 실행명령어, docker run에 의해 덮어쓰여질 수 있는 바뀔 수 있는 명령어. 1회만 실행
      2. ENTRYPOINT: container 생성시 실행명령어, 항상 실행되는 명령어. docker run명령어가 있어도 1회만 실행
   5. 외부용X 서 입력하는 port번호인 `EXPOSE`할 app의 port를 `5005`로 지정
      1. EXPOSE: 호스트에 공개X매핑X, 연계되는 타 container와의 연결 or 포트매핑시 사용될 port를, image빌드시 지정만 해주는 container port설정
         - **여기선 EXPOSE만 노출(image빌드시 노출port만 지정) -> docker-compose.yml에서 `ports [host웹서버port]:[expose컨테이너웹서버port]`에 지정**
         - **포트 매핑을 하지 않는 이상, 외부에서의 접속은 불가능하다. 포트매핑은 Dockerfile에는 지정불가능하고 `docker run -p`시만 가능하다** 
      2. `docker -p` 옵션 or docker-compose의 `ports`만 or a:b 형식으로 host의 포트와 매핑
   6. 컨테이너 속 웹서버 실행 명령어를 `CMD ["",""]` 형식으로 실행
      1. **실행 전 웹서버 설치 -> pip freeze >**
      2. 직접 terminal에서 실행해보고, `CMD []`안에 커맨드 복사 후 형식에 맞추도록 변경
         - manage.py:app으로 하면 안됨. `manage:app`로서 앞에 **from에 적히는 모듈명만 작성해야한다.**
      ```python
      CMD []
      # 윈도우에서는 gunicorn 실행 안됨.
      pip install gunicorn
      pip freeze > requirements.txt
      
      gunicorn -w 3 -b 0.0.0.0:5005 manage:app
      
      # CMD [gunicorn -w 3 -b 0.0.0.0:5005 manage.py:app]
      CMD ["gunicorn", "-w", "3", "-b", "0.0.0.0:5005", "manage.py:app"]
      ```
      
   ```dockerfile
   FROM python:3.9
   COPY . /app
   WORKDIR /app
   RUN pip install -r requirements.txt
   EXPOSE 5005
   CMD ["gunicorn", "-w", "3", "-b", "0.0.0.0:5005", "manage:app"]
   ```
   

### Dockerfile build기반 app컨테이너 with ports매핑 + image기반 Postgre컨테이너를 동시에 띄우는 docker-compose
1. 작성한 `app Dockerfile`을 인식할 수 있는 root에서 `docker-compose.yml`파일을 생성
2. `services`에 각종 띄울 컨테이너들을 작성한다
   - **나의 app은 따로 기반 image가 없기 때문에 `python image기반으로 [Dockerfile]`을 작성 후 `[build: .]`등의 dockerfile을 지정해서 conatiner를 띄우고*
   - **데이터베이스는 기반image가 존재하여, `build옵션 없이 [image: DB-BASE-image]`를 지정해서 conatiner를 띄울 것이다.**
   ```dockerfile
   version: '3.1'
   
   services:
     app:
       build: video
       restart: always

     postgres:
       image: postgres:10
       restart: always
   ```
   
3. app컨테이너 설정
   1. build+restart 옵션 외에 **`depends_on:` 을 지정하여, DB컨테이너가 띄워진 뒤, 띄우도록 설정한다**
   2. **띄워질 때, `ports`를 지정하여 `접속할host의 port : expose된 conatiner port`를 연결한다**
      - ports의 변수는 `""`의 따옴표를 사용하는 것이 특징
   3. app을 띄울 때, `노출되서는 안되며 바뀔 수 있는 것 변수들(URI, SECREY_KEY)`을 `환경변수${}`로 지정하여 작성하고, **환경변수를 작성**을 준비한다
   ```dockerfile
   services:
     app:
       build: .
       restart: always
       depends_on:
         - postgres
       ports:
         - "5005:5005"
       environment:
         - SQLALCHEMY_DATABASE_URI=${DATABASE_URI}
         - SECRET_KEY=${SECRET_KEY}
   ```
   
4. postgres 설정
   1. image기반으로 container를 띄우며 :10 버전을 쓴다
   2. ports매핑은 내부expose는 "5432"가 고정이므로, 외부접속할 host포트를 "5434"정도로 다르게 매핑해준다.
   3. 환경변수는 user/password가 기본이다.(DB명은 app에서 create_all시 지정한 db가 자동 생성)
   ```dockerfile
   postgres:
    image: postgres:10
    restart: always
    ports:
      - "5434:5432"
    environment:
      - POSTGRES_USER=%{POSTGRES_USER}
      - POSTGRES_PASSWORD=%{POSTGRES_PASSWORD}
   ```
   
### docker-compose에 작성한 환경변수를 .env에 기록하여 환경변수에 load되도록 하기
1. `.env`파일을 만들고, gitignore에 추가한 뒤, docker-compose에 작성된 환경변수들을 복사해간다
   - .env파일가 안열리면 `우클릭 > override file type > Dotenv`
   ![img.png](images/doenv.png)
   ![img.png](images/dotenv2.png)

2. 따옴표 없이 환경변수의 내용을 채운다.
3. 이미 환경변수 없이 하드코딩으로 작성된 변수가 있을 경우, 다시 .env에서 python파일로 가져다 쓰도록 `os.getenv('')`로 변경한다
   - **db의 포트는 docker-compose 중`외부 커스텀 port5434:컨테이너내부포트5432고정` 중에 외부커스텀포트5434를 갖다써서 만들어야한다**
   ```python
   # .env
   DATABASE_URI=postgresql://testuser:testpassword@postgres:5434
   SECRET_KEY=
   
   # vidoe_api/config.py
   class Config:
       SECRET_KEY = '437374e9d2dc467abe0d0ab9b985c742'
   ```         
   ```python
   # vidoe_api/config.py
   import os
   
   
   class Config:
       SECRET_KEY = os.getenv('SECRET_KEY')
       SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URI')
   ```
   
4. Secret키는 terminal - console에서 uuid로 작성해준다.
   ```python
   import uuid
   uuid.uuid4().hex
   'f8e4a74e907b42dc817cfb5055fc576e'
   ```
   - .env의 내용은 "" 쌍따옴표 때고 입력
   ```yaml
   DATABASE_URI=postgresql://testuser:testpassword@postgres:5432
   SECRET_KEY=f8e4a74e907b42dc817cfb5055fc576e
   ```
   
5. **os.getenv는 `docker-compose 작동시 linux에 export되는 환경변수`들이기 때문에, 일반 작동시에도 작동하도록 Config 클래스의 상수들에게 `or 'HARD-CODING'`을 임시로 작성해주자.**
   - 그래야 **docker-compose없이 앱을 작동**했을 때 기본값이 들어갈 것이다.
   ```python
   # __init__.py
   engine = create_engine('sqlite:///db.sqlite')
   ```
   ```python
   # __init__.py
   engine = create_engine(Config.SQLALCHEMY_DATABASE_URI)

   class Config:
       SECRET_KEY = os.getenv('SECRET_KEY') or 'secret_key'
       SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URI') or 'sqlite:///db.sqlite'
   ```

6. docker-compose의 postgres에서 사용된 환경변수들 -> python에서는 사용안되니, 편하게 작성
   - **postgre DATABASE_URI에 사용되는 `유저:password`를 사용한다** 
   ```yaml
   DATABASE_URI=postgresql://testuser:testpassword@postgres:5432
   SECRET_KEY=f8e4a74e907b42dc817cfb5055fc576e
   
   POSTGRES_USER=testuser
   POSTGRES_PASSWORD=testpassword
   ```
   

### docker-compose 실행
1. 버전 확인 후 실행
   ```shell
   
   docker --version
   # Docker version 20.10.13, build a224086
   docker-compose --version
   # docker-compose version 1.29.2, build 5becea4c
   
   docker-compose up
   ```
   ```
   # 터미널 새로 열어서 ps확인
   # docker-compse ps
   # docker 컨테이너 확인은 docker ps -a로 다 하는 것이 방법이다.
   docker ps -a
   #          Name                   Command           State           Ports
   # --------------------------------------------------------------------------------
   # flaskproject_app_1       gunicorn -w 3 -b         Up      0.0.0.0:5005->5005/tcp
   #                          0.0.0.0:5 ...
   # flaskproject_postgres_   docker-entrypoint.sh     Up      0.0.0.0:5434->5432/tcp
   # 1                        postgres
   ```
   
2. **api는 문서ui에 접속해서 접속 확인**
   - app의 컨테이너는 모든외부포트(0.0.0.0)`:5005`로 열여있고, 포트매핑을 `"5005:5005"`로 했으니, **host의주소 `127.0.0.1` + 컨테이너 매핑 host 포트 `:5005`로 접속한다**
   ```shell
   http://127.0.0.1:5005/swagger-ui
   http://localhost:5005/swagger-ui
   ```
   ![img.png](images/docker-compose_swagger.png)


### github에 프로젝트 share(push) 후 AWS ssh clone + docker-compose로 실행(DB부터 실행)
1. 상단 `Git` > github > share project on github
2. aws서버 접속(ssh configure에서 퍼블릭 IPv4 or 퍼블릭 IPv4 DNS를 보고 수정하여 접속)
3. github의 ssh주소로 프로젝트 clone
   ```shell
   git@github.com:is2js/flask_video_api.git
   ```
4. root폴더로 이동 후, docker 버전 확인후 `-d [postgres서비스]`으로 **databse container만 먼저 실행**
   ```shell
   ubuntu@ip-172-31-10-50:~$ cd flask_video_api/
   ubuntu@ip-172-31-10-50:~/flask_video_api$ docker --version
   Docker version 20.10.22, build 3a2c30b
   ubuntu@ip-172-31-10-50:~/flask_video_api$ docker-compose --version
   docker-compose version 1.25.0-rc2, build 661ac20e
   ubuntu@ip-172-31-10-50:~/flask_video_api$ docker-compose up -d postgres
   ```
   - 실행중인 container 확인은 `docker ps -a`로
   ```shell
   docker ps -a
   ```
   
4. **`ls -al`로 `.env` 확인 후, `vi .env`로 작성작성(원래는 없어야하는데, 따라옴)**
   - 환경변수 등을 확인한다.
   ```shell
   ls -al
   vi .env
   ```
5. **app 서비스 컨테이너도 추가 실행 `-d app`**
   ```shell
   docker-compose up -d app
   ```
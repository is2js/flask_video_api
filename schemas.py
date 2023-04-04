from marshmallow import Schema, fields, validate

class VideoSchema(Schema):
    # id와 fk는 payload에서 받지않고, token/url_path로부터 받을 것이므로, 역직렬화(view->back)에서는 안받도록 해준다.
    id = fields.Integer(dump_only=True)
    user_id = fields.Integer(dump_only=True)
    # nullable=False는 required=True로 대응한다.
    # String(250)은 validate로 대응한다.
    name = fields.String(required=True, validate=[validate.Length(max=250)])
    description = fields.String(required=True, validate=[validate.Length(max=500)])

    message = fields.String(dump_only=True)


class UserSchema(Schema):
    # User route는 id를 직렬화하지 않고 token만 내보낸다. -> 역직렬화용 -> id/fk 다 생략?!
    name = fields.String(required=True, validate=[validate.Length(max=250)])
    email = fields.String(required=True, validate=[validate.Length(max=250)])
    # password의 경우 read되면 안되므로 load_only 옵션을 줘야한다.
    password = fields.String(required=True, validate=[validate.Length(max=100)], load_only=True)
    # relationship은 Nested()로 대응하며, one-to-many일 경우, many=True옵션을 추가하고,
    # - 기본적으로 dump_only(직렬화 전용)으로 만들어준다. (차후 직렬화 대비?)
    videos = fields.Nested(VideoSchema, many=True, dump_only=True)

class AuthSchema(Schema):
    access_token = fields.String(dump_only=True)

    message = fields.String(dump_only=True)
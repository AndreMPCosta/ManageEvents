from datetime import timedelta

from flask import request
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    jwt_refresh_token_required,
    get_jwt_identity,
    jwt_required,
    get_raw_jwt,
)
from flask_restful import Resource

from blacklist import BLACKLIST
from models.user import UserModel
from schemas.user import UserSchema
from utils.password_manager import encrypt_password, check_encrypted_password
from utils.validator import validate_request

USER_ALREADY_EXISTS = "A user with that username already exists."
CREATED_SUCCESSFULLY = "User created successfully."
USER_NOT_FOUND = "User not found."
USER_DELETED = "User deleted."
INVALID_CREDENTIALS = "Invalid credentials!"
USER_LOGGED_OUT = "{} successfully logged out."

user_schema = UserSchema()


class UserRegister(Resource):
    @classmethod
    def post(cls):
        user_json = request.get_json()
        if not validate_request(user_json, UserModel):
            return {'message': 'Request invalid, please re-check your parameters.'}, 400
        user_json['password'] = encrypt_password(user_json['password'])
        user = user_schema.load(user_json)

        if UserModel.find_by_username(user.username):
            return {"message": USER_ALREADY_EXISTS}, 400

        user.save_to_db()

        return {"message": CREATED_SUCCESSFULLY}, 201


class User(Resource):
    @classmethod
    def get(cls, user_id: int):
        user = UserModel.find_by_id(user_id)
        if not user:
            return {"message": USER_NOT_FOUND}, 404

        return user_schema.dump(user), 200

    # Internal if there is a necessity to delete an user
    @classmethod
    def delete(cls, user_id: int):
        user = UserModel.find_by_id(user_id)
        if not user:
            return {"message": USER_NOT_FOUND}, 404

        user.delete_from_db()
        return {"message": USER_DELETED}, 200


class UserLogin(Resource):
    @classmethod
    def post(cls):
        user_json = request.get_json()
        if not validate_request(user_json, UserModel):
            return {'message': 'Request invalid, please re-check your parameters.'}, 400
        user_data = user_schema.load(user_json)

        user = UserModel.find_by_username(user_data.username)

        if user and check_encrypted_password(user_data.password, user.password):
            # token is valid for one week, generally it is minutes, but since this is not a production app, one week is
            # good enough
            access_token = create_access_token(identity=user.id, fresh=True, expires_delta=timedelta(days=7))
            refresh_token = create_refresh_token(user.id, expires_delta=False)
            return {"access_token": access_token, "refresh_token": refresh_token}, 200

        return {"message": INVALID_CREDENTIALS}, 401


class UserLogout(Resource):
    @classmethod
    @jwt_required
    def post(cls):
        jti = get_raw_jwt()["jti"]
        user_id = get_jwt_identity()
        BLACKLIST.add(jti)
        user = UserModel.find_by_id(user_id)
        return {"message": USER_LOGGED_OUT.format(user.username)}, 200


class TokenRefresh(Resource):
    @classmethod
    @jwt_refresh_token_required
    def post(cls):
        current_user = get_jwt_identity()
        new_token = create_access_token(identity=current_user, fresh=False)
        return {"access_token": new_token}, 200

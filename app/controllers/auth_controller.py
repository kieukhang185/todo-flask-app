from flask import request
from flask_restx import Namespace, Resource, fields
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from datetime import timedelta
from ..extensions import mongo, bcrypt, api

auth_ns = Namespace('auth', description='Authentication operations', decorators=[jwt_required(locations=('cookies','headers'))])

auth_model = auth_ns.model('Auth', {
    'username': fields.String(required=True),
    'password': fields.String(required=True)
})

@auth_ns.route('/login')
class Login(Resource):
    @auth_ns.expect(auth_model)
    def post(self):
        data = request.get_json()
        user = mongo.db.users.find_one({'username': data.get('username')})
        if not user or not bcrypt.check_password_hash(user['password'], data.get('password')):
            return {'message': 'Invalid credentials'}, 401
        token = create_access_token(identity=user['username'], expires_delta=timedelta(hours=1))
        return {'access_token': token}, 200

@auth_ns.route('/logout')
class Logout(Resource):
    @jwt_required()
    def post(self):
        # For JWT, client should discard token
        return {'message': 'Logout successful'}, 200

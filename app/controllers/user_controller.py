from flask import request
from flask_restx import Namespace, Resource, fields
from flask_jwt_extended import jwt_required, get_jwt_identity
from ..extensions import mongo, bcrypt, api
from ..utils.decorators import admin_required

user_ns = Namespace('users', description='User management', decorators=[jwt_required(locations=('cookies','headers'))])

user_model = user_ns.model('User', {
    'username': fields.String(required=True),
    'email': fields.String(required=True),
    'password': fields.String(required=True),
    'role': fields.String(enum=['admin','user'], default='user')
})
profile_model = user_ns.model('Profile', {
    'email': fields.String(),
    'password': fields.String()
})
role_model = user_ns.model('Role', {
    'role': fields.String(enum=['admin','user'], required=True)
})

@user_ns.route('/')
class UserList(Resource):
    @jwt_required()
    @admin_required
    def get(self):
        users = list(mongo.db.users.find({}, {'password': 0}))
        for u in users:
            u['_id'] = str(u['_id'])
        return users, 200

    @user_ns.expect(user_model)
    @jwt_required()
    @admin_required
    def post(self):
        data = request.get_json()
        if mongo.db.users.find_one({'username': data.get('username')}):
            return {'message': 'User already exists'}, 400
        hashed = bcrypt.generate_password_hash(data.get('password')).decode('utf-8')
        user = {
            'username': data.get('username'),
            'password': hashed,
            'email': data.get('email'),
            'role': data.get('role', 'user'),
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        }
        mongo.db.users.insert_one(user)
        return {'message': 'User created'}, 201

@user_ns.route('/<string:username>')
class User(Resource):
    @jwt_required()
    def get(self, username):
        current = get_jwt_identity()
        if current != username:
            user = mongo.db.users.find_one({'username': current})
            if not user or user.get('role') != 'admin':
                return {'message': 'Access denied'}, 403
        u = mongo.db.users.find_one({'username': username}, {'password': 0})
        if not u:
            return {'message': 'User not found'}, 404
        u['_id'] = str(u['_id'])
        return u, 200

    @user_ns.expect(profile_model)
    @jwt_required()
    def put(self, username):
        current = get_jwt_identity()
        if current != username:
            user = mongo.db.users.find_one({'username': current})
            if not user or user.get('role') != 'admin':
                return {'message': 'Access denied'}, 403
        data = request.get_json()
        update = {}
        if 'email' in data:
            update['email'] = data['email']
        if 'password' in data:
            update['password'] = bcrypt.generate_password_hash(data['password']).decode('utf-8')
        if update:
            mongo.db.users.update_one({'username': username}, {'$set': update})
        return {'message': 'User updated'}, 200

@user_ns.route('/<string:username>/role')
class UserRole(Resource):
    @user_ns.expect(role_model)
    @jwt_required()
    @admin_required
    def patch(self, username):
        data = request.get_json()
        if not mongo.db.users.find_one({'username': username}):
            return {'message': 'User not found'}, 404
        mongo.db.users.update_one({'username': username}, {'$set': {'role': data.get('role')}})
        return {'message': 'Role updated'}, 200


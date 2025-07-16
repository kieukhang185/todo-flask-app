from flask import request
from flask_restx import Namespace, Resource, fields
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
from ..extensions import mongo, api
from ..utils.sequence import get_next_sequence

todo_ns = Namespace('todos', description='ToDo operations', decorators=[jwt_required(locations=('cookies','headers'))])

comment_model = todo_ns.model('Comment', {
    'commenter': fields.String,
    'content': fields.String,
    'timestamp': fields.DateTime
})

todo_model = todo_ns.model('Todo', {
    'title': fields.String(required=True),
    'description': fields.String,
    'status': fields.String(enum=['new','in-progress','reject','done','under-review'], default='new'),
    'label': fields.String,
    'assignee': fields.String,
    'type': fields.String(enum=['task','sub-task','epic','bug'], required=True),
    'epic_id': fields.String
})

add_comment = todo_ns.model('AddComment', { 'content': fields.String(required=True) })

@todo_ns.route('/')
class TodoList(Resource):
    @jwt_required()
    def get(self):
        filters = {k: v for k, v in request.args.items() if k in ['status','label','reporter','assignee','type','epic_id']}
        todos = list(mongo.db.todos.find(filters))
        for t in todos:
            t['_id'] = str(t['_id'])
        return todos, 200

    @todo_ns.expect(todo_model)
    @jwt_required()
    def post(self):
        data = request.get_json()
        username = get_jwt_identity()
        prefix_map = {'task':'TASK','epic':'EPIC','sub-task':'SUB','bug':'BUG'}
        prefix = prefix_map[data.get('type')]
        seq = get_next_sequence(prefix)
        todo_id = f"{prefix}-{seq:02d}"

        if data.get('type') in ['task','bug'] and not data.get('epic_id'):
            return {'message': 'epic_id required for tasks and bugs'}, 400

        todo = {
            'id': todo_id,
            'title': data.get('title'),
            'description': data.get('description'),
            'status': data.get('status','new'),
            'label': data.get('label'),
            'reporter': username,
            'assignee': data.get('assignee'),
            'type': data.get('type'),
            'epic_id': data.get('epic_id'),
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow(),
            'comments': []
        }
        mongo.db.todos.insert_one(todo)
        return {'message': 'ToDo created', 'id': todo_id}, 201

@todo_ns.route('/<string:todo_id>')
class Todo(Resource):
    @jwt_required()
    def get(self, todo_id):
        todo = mongo.db.todos.find_one({'id': todo_id})
        if not todo:
            return {'message':'Not found'},404
        todo['_id'] = str(todo['_id'])
        return todo,200

    @todo_ns.expect(todo_model)
    @jwt_required()
    def put(self, todo_id):
        todo = mongo.db.todos.find_one({'id': todo_id})
        if not todo:
            return {'message':'Not found'},404
        user = mongo.db.users.find_one({'username': get_jwt_identity()})
        if get_jwt_identity() not in [todo['reporter'], todo.get('assignee')] and user.get('role')!='admin':
            return {'message':'Access denied'},403
        data = request.get_json()
        data['updated_at'] = datetime.utcnow()
        mongo.db.todos.update_one({'id': todo_id}, {'$set': data})
        return {'message':'ToDo updated'},

todo_ns.route('/<string:todo_id>/comments')
class TodoComment(Resource):
    @todo_ns.expect(add_comment)
    @jwt_required()
    def post(self, todo_id):
        todo = mongo.db.todos.find_one({'id': todo_id})
        if not todo:
            return {'message':'Not found'},404
        comment = {
            'commenter': get_jwt_identity(),
            'content': request.get_json().get('content'),
            'timestamp': datetime.utcnow()
        }
        mongo.db.todos.update_one({'id': todo_id}, {'$push': {'comments': comment}})
        return {'message':'Comment added'},201

# Register namespace
api.add_namespace(todo_ns, path='/todos')

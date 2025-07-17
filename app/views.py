from flask import Blueprint, render_template, redirect, url_for, request, session, flash, make_response
from flask_jwt_extended import (
    create_access_token, unset_jwt_cookies,
    jwt_required, get_jwt_identity, set_access_cookies
)
from .extensions import mongo, bcrypt

views = Blueprint('views', __name__)

# Home → redirect to ToDo list
@views.route('/')
def home():
    return redirect(url_for('views.list_todos'))

#  — AUTH VIEWS —

@views.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        uname = request.form['username']
        pw    = request.form['password']
        user  = mongo.db.users.find_one({'username': uname})
        if user and bcrypt.check_password_hash(user['password'], pw):
            token = create_access_token(identity=uname)
            resp = make_response(redirect(url_for('views.list_todos')))
            # This actually plants the cookie the @jwt_required decorator will read:
            set_access_cookies(resp, token)
            session['username'] = uname
            return resp
        flash('Invalid credentials')
    return render_template('login.html')

@views.route('/logout')
def logout():
    session.clear()
    resp = make_response(redirect(url_for('views.login')))
    unset_jwt_cookies(resp)
    return resp

@views.route('/register', methods=['GET','POST'])
def register():
    if request.method == 'POST':
        uname = request.form['username']
        email = request.form['email']
        pw    = bcrypt.generate_password_hash(request.form['password']).decode()
        if mongo.db.users.find_one({'username': uname}):
            flash('Username taken')
        else:
            mongo.db.users.insert_one({
                'username': uname,
                'email': email,
                'password': pw,
                'role': 'user'
            })
            flash('Registered! Please log in.')
            return redirect(url_for('views.login'))
    return render_template('register.html')

#  — PROFILE VIEW —

@views.route('/profile', methods=['GET','POST'])
@jwt_required(locations=("cookies",))
def profile():
    cur = get_jwt_identity()
    user = mongo.db.users.find_one({'username': cur})
    if request.method == 'POST':
        updates = {}
        if request.form.get('email'):
            updates['email'] = request.form['email']
        if request.form.get('password'):
            updates['password'] = bcrypt.generate_password_hash(
                request.form['password']
            ).decode()
        if updates:
            mongo.db.users.update_one({'username': cur}, {'$set': updates})
            flash('Profile updated')
            return redirect(url_for('views.profile'))
    return render_template('profile.html', user=user)

#  — ToDo VIEWS —

@views.route('/todos')
@jwt_required(locations=("cookies",))
def list_todos():
    todos = list(mongo.db.todos.find()) # get all todo exist
    return render_template('todos/list.html', todos=todos)

@views.route('/todos/new', methods=['GET','POST'])
@jwt_required(locations=("cookies",))
def new_todo():
    if request.method == 'POST':
        title       = request.form['title']
        description = request.form.get('description')
        type_       = request.form['type']
        status      = request.form['status']
        assignee    = request.form.get('assignee') or None
        epic_id     = request.form.get('epic_id') or None  # only relevant for tasks/bugs
        reporter    = get_jwt_identity()

        # enforce epic linkage for tasks & bugs
        # if type_ in ('task', 'bug') and not epic_id:
        #     flash('You must select an epic for tasks and bugs', 'danger')
        #     return redirect(url_for('views.new_todo'))

        # generate ID
        prefix_map = {'epic':'EPIC', 'task':'TASK', 'sub-task':'SUB', 'bug':'BUG'}
        prefix = prefix_map[type_]
        seq = get_next_sequence(prefix)
        todo_id = f"{prefix}-{seq:02d}"

        todo = {
            'id':         todo_id,
            'title':      title,
            'description': description,
            'status':     status,
            'label':      request.form.get('label'),
            'reporter':   reporter,
            'assignee':   assignee,
            'type':       type_,
            'epic_id':    epic_id,
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow(),
            'comments':   []
        }
        mongo.db.todos.insert_one(todo)
        flash(f'ToDo {todo_id} created!', 'success')
        return redirect(url_for('views.list_todos'))

    # GET: populate epics for the form
    epics = list(mongo.db.todos.find({'type': 'epic'}))
    return render_template('todos/form.html', todo=None, epics=epics)

@views.route('/todos/<todo_id>')
@jwt_required(locations=("cookies",))
def detail_todo(todo_id):
    todo = mongo.db.todos.find_one({'id': todo_id})
    return render_template('todos/detail.html', todo=todo)

@views.route('/todos/<todo_id>/edit', methods=['GET','POST'])
@jwt_required(locations=("cookies",))
def edit_todo(todo_id):
    todo = mongo.db.todos.find_one({'id': todo_id})
    if request.method == 'POST':
        # apply edits…
        return redirect(url_for('views.detail_todo', todo_id=todo_id))
    return render_template('todos/form.html', todo=todo)

@views.route('/todos/<todo_id>/assign', methods=['POST'])
@jwt_required(locations=('cookies','headers'))
def assign_to_me(todo_id):
    current = get_jwt_identity()
    # Only assign if not already assigned to this user
    todo = mongo.db.todos.find_one({'id': todo_id})
    if not todo:
        flash('ToDo not found.', 'danger')
    elif todo.get('assignee') == current:
        flash('You are already the assignee.', 'info')
    else:
        mongo.db.todos.update_one(
            {'id': todo_id},
            {'$set': {'assignee': current, 'updated_at': datetime.utcnow()}}
        )
        flash(f'ToDo {todo_id} assigned to you.', 'success')
    return redirect(url_for('views.list_todos'))

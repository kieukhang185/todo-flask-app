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
            return resp
        flash('Invalid credentials')
    return render_template('login.html')

@views.route('/logout')
def logout():
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
    todos = list(mongo.db.todos.find({'reporter': get_jwt_identity()}))
    return render_template('todos/list.html', todos=todos)

@views.route('/todos/new', methods=['GET','POST'])
@jwt_required(locations=("cookies",))
def new_todo():
    if request.method == 'POST':
        # mirror your API post logic here…
        # e.g. collect form data, insert into mongo, then redirect
        return redirect(url_for('views.list_todos'))
    return render_template('todos/form.html', todo=None)

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

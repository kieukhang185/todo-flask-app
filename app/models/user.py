import os
from datetime import datetime
from ..extensions import bcrypt, mongo


def create_default_admin():
    # Read default admin credentials from environment
    username = os.environ['ADMIN_USERNAME']
    password = os.environ['ADMIN_PASSWORD']
    email = os.environ['ADMIN_EMAIL']
    if not mongo.db.users.find_one({'username': username}):
        hashed = bcrypt.generate_password_hash(password).decode('utf-8')
        admin = {
            'username': username,
            'password': hashed,
            'email': email,
            'role': 'admin',
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        }
        mongo.db.users.insert_one(admin)
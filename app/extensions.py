from flask_pymongo import PyMongo
from flask_jwt_extended import JWTManager
from flask_bcrypt import Bcrypt
from flask_restx import Api

mongo = PyMongo()
jwt = JWTManager()
bcrypt = Bcrypt()

authorizations = {
    'BearerAuth': {
        'type': 'apiKey',
        'in':   'header',
        'name': 'Authorization',
        'description': "Add a JWT with **Bearer &lt;JWT&gt;**"
    }
}

api = Api(
    title='ToDo API',
    version='1.0',
    description='Flask-based ToDo management API with JWT authentication and MongoDB',
    prefix='/api',
    doc='/api',                # disable automatic docs mount
    authorizations=authorizations,
    security='BearerAuth'
)
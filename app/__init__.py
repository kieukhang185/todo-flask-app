# app/__init__.py

from flask import Flask, request, redirect, url_for
from flask_jwt_extended import (
    verify_jwt_in_request, jwt_required,
    JWTManager, get_jwt_identity
)
from .config import Config
from .extensions import mongo, jwt, bcrypt, api
from .models import create_default_admin
from .controllers import auth_ns, user_ns, todo_ns
from .views import views

# class CustomJSONEncoder(JSONEncoder):
#     def default(self, obj):
#         if isinstance(obj, datetime):
#             # e.g. "2025-07-16T15:02:51Z"
#             return obj.isoformat() + 'Z'
#         return super().default(obj)

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Initialize extensions
    mongo.init_app(app)
    jwt.init_app(app)         # 'jwt' is an instance of JWTManager
    bcrypt.init_app(app)
    api.init_app(app)

    # Register API namespaces under /api
    api.add_namespace(auth_ns,  path='/auth')
    api.add_namespace(user_ns,  path='/users')
    api.add_namespace(todo_ns,  path='/todos')

    # Callback for missing or invalid JWT in cookie/header
    @jwt.unauthorized_loader
    def missing_token_callback(error_string):
        if request.path.startswith('/api/'):
            return {'msg': error_string}, 401
        return redirect(url_for('views.login'))

    @jwt.invalid_token_loader
    def invalid_token_callback(error_string):
        if request.path.startswith('/api/'):
            return {'msg': error_string}, 401
        return redirect(url_for('views.login'))

    # Callback for expired token
    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        if request.path.startswith('/api/'):
            return {'msg': 'Token has expired'}, 401
        return redirect(url_for('views.login'))

    # Protect all /api/* except /api/auth/* and swagger JSON
    @app.before_request
    def require_api_authentication():
        path = request.path
        if (
            path.startswith('/api/')
            and not path.startswith('/api/auth/')
            and path not in ('/api', '/api/')
            and not path.endswith('swagger.json')
        ):
            verify_jwt_in_request(locations=('cookies','headers'))

    @app.context_processor
    def inject_current_user():
        try:
            # if there's a valid JWT cookie/header, this will succeed
            verify_jwt_in_request(locations=('cookies','headers'))
            user = get_jwt_identity()
        except:
            user = None
        return dict(current_user=user)

    # Serve Swagger UI at /api behind JWT
    @app.route('/api', strict_slashes=False)
    @jwt_required(locations=('cookies','headers'))
    def swagger_ui():
        return api.render_doc()

    # Register your HTML GUI routes
    app.register_blueprint(views)

    # Ensure default admin user exists
    with app.app_context():
        create_default_admin()

    return app

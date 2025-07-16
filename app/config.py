import os
import datetime

class Config:
    # Load all secrets and connection strings from environment
    SECRET_KEY = os.environ['SECRET_KEY']
    MONGO_URI = os.environ['MONGO_URI']
    JWT_SECRET_KEY = os.environ['JWT_SECRET_KEY']
    JWT_ACCESS_COOKIE_PATH = '/'       # make the cookie valid app-wide
    JWT_ACCESS_TOKEN_EXPIRES = datetime.timedelta(seconds=1800)
    WT_TOKEN_LOCATION = ['cookies']
    WT_COOKIE_SECURE = False          # for local dev; set True under HTTPS
    SWAGGER_UI_DOC_EXPANSION = 'list'
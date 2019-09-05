import os

DEBUG = True

SQLALCHEMY_DATABASE_URI = 'postgresql://{user}:{pw}@{host}:{port}/{db}'.format(
    user=os.environ.get('user'),
    pw=os.environ.get('pw'),
    host=os.environ.get('host'),
    port=os.environ.get('port'),
    db=os.environ.get('db')
)

SQLALCHEMY_TRACK_MODIFICATIONS = False
PROPAGATE_EXCEPTIONS = True

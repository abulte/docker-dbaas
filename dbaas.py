from flask.ext.script import Manager

from webapp import app

manager = Manager(app)

BASE_URL = 'http://localhost:4243'

@manager.command
def create(ttype):
    """dbaas create DB_TYPE"""
    print ttype

if __name__ == "__main__":
    manager.run()
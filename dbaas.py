import time
from docker import Client
from flask.ext.script import Manager
from termcolor import colored

from webapp import app

manager = Manager(app)

MEM_LIMIT = 256*1024*1024
BASE_URL = 'http://172.17.42.1:4243'
MYSQL_IMG = 'dbaas/mysql'
MYSQL_IMG_SRC = 'github.com/abulte/docker-mysql'
MYSQL_CRED = ('root', 'root4mysql')

c = Client(base_url=BASE_URL, version='1.3')

def ok():
    return colored('[OK]', 'green')

def ko():
    return colored('[KO]', 'red')

def create_mysql():
    if len(c.images(name=MYSQL_IMG)) == 0:
        print 'Fetching image from index.docker.io...'
        print c.pull(MYSQL_IMG)
        print '%s Image pulled as %s' % (ok(), MYSQL_IMG)
    return c.create_container(MYSQL_IMG, '/usr/sbin/mysqld', detach=True, mem_limit=MEM_LIMIT)

def _extract_info(c_id):
    data = c.inspect_container(c_id)
    if not data['State']['Running']:
        print '%s Container is not running' % ko()
        return False
    ip = data['NetworkSettings']['IPAddress']
    mysql_port = data['NetworkSettings']['PortMapping']['Tcp'].get('3306', None)
    return ip, mysql_port

@manager.command
def test_container(c_id, ttype, quiet=False):
    if ttype == 'mysql':
        try:
            import mysql.connector
            info = _extract_info(c_id)
            if not info: return 1
            cnx = mysql.connector.connect(user=MYSQL_CRED[0], password=MYSQL_CRED[1],
                                      host=info[0], # database='users'
                                    )
            cnx.close()
            if not quiet:
                print '%s Connection successful to %s' % (ok(), c_id)
            return True
        except Exception, e:
            if not quiet:
                print '%s %s' % (ko(), e)
    return False

@manager.command
def start(ttype):
    """dbaas start DB_TYPE"""
    if ttype == 'mysql':
        container = create_mysql()
    else:
        print "%s Unsupported db type provided: %s" % (ko(), ttype)
        return 1
    c.start(container['Id'])
    print "%s Started container %s" % (ok(), container['Id'])
    print 'Waiting for MySQL to boot...'
    time.sleep(5)
    return test_container(container['Id'], 'mysql')

@manager.command
def test():
    print 'this is a test'

@manager.command
def list(type='all'):
    print c.containers()

@manager.command
def inspect(container_id):
    data = c.inspect_container(container_id)
    print data

if __name__ == "__main__":
    manager.run()

from docker import Client
from webapp import app
from termcolor import colored


def dc():
    return Client(base_url=app.config.get('BASE_URL'), version='1.3')

def ok():
    return colored('[OK]', 'green')

def ko():
    return colored('[KO]', 'red')

def _format_container(raw):
    # app.logger.debug(raw)
    running = raw['State']['Running']
    c_id = raw['ID'][:12]
    if not running:
        return {'id': c_id, 'running': False}
    else:
        return {
            'id': c_id,
            'running': True,
            'ip': raw['NetworkSettings']['IPAddress'],
            'db_port': raw['NetworkSettings']['PortMapping']['Tcp'].get('3306', None),
            'created': raw['Created']
        }

def stop_container(c_id):
    dc().stop(c_id)
    return True

def start_container(c_id):
    dc().start(c_id)
    return True

def remove_container(c_id):
    dc().remove_container(c_id)
    return True

def inspect_container(container_id):
    raw = dc().inspect_container(container_id)
    return _format_container(raw)

def get_containers(details=False):
    cs = dc().containers(all=True)
    if not details:
        return cs
    else:
        detail_containers = []
        for c in cs:
            app.logger.debug(c)
            details = inspect_container(c['Id'])
            details['status'] = c['Status']
            detail_containers.append(details)
    return detail_containers

def _create_mysql(quiet=True):
    if len(dc().images(name=app.config.get('MYSQL_IMG'))) == 0:
        if not quiet: print 'Fetching image from index.docker.io...'
        dc().pull(app.config.get('MYSQL_IMG'))
        if not quiet: print '%s Image pulled as %s' % (ok(), app.config.get('MYSQL_IMG'))
    return dc().create_container(app.config.get('MYSQL_IMG'), '/usr/sbin/mysqld', detach=True, mem_limit=app.config.get('MEM_LIMIT'))

def create_container(dbtype, quiet=True):
    if dbtype == 'mysql':
        container = _create_mysql(quiet)
    else:
        if not quiet: 
            print "%s Unsupported db type provided: %s" % (ko(), dbtype)
            return 1
        else:
            raise Exception('Unsupported db type provided: %s' % dbtype)
    start_container(container['Id'])
    return container

def test_container(c_id, ttype, quiet=True):
    if ttype == 'mysql':
        try:
            import mysql.connector
            info = inspect_container(c_id)
            if not quiet and (not info or not info['running']): 
                return 1
            elif not info:
                raise Exception('No container by id')
            elif not info['running']:
                return False
            cnx = mysql.connector.connect(user=app.config.get('MYSQL_CRED')[0], 
                                        password=app.config.get('MYSQL_CRED')[1],
                                        host=info['ip'], # database='users'
                                    )
            cnx.close()
            if not quiet: print '%s Connection successful to %s' % (ok(), c_id)
            return True
        except Exception, e:
            if not quiet: print '%s %s' % (ko(), e)
    return False



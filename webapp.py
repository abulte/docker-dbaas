import docker_lib as docker
from flask import Flask, render_template, request, redirect, \
    url_for, flash, jsonify
app = Flask(__name__)

app.debug = True

app.config.update(
    SECRET_KEY = 'sLdNV5V33lFAaDKzswFVt6NG2ciz1OrJ5IfAwgyr',
    MEM_LIMIT = 256*1024*1024,
    BASE_URL = 'http://172.17.42.1:4243',
    MYSQL_IMG = 'dbaas/mysql',
    MYSQL_IMG_SRC = 'github.com/abulte/docker-mysql',
    MYSQL_CRED = ('root', 'root4mysql')
)

@app.route('/')
def index():
    containers = docker.get_containers(details=True)
    # app.logger.debug(containers)
    return render_template('index.html', containers=containers)

@app.route('/stop/<c_id>')
def stop(c_id):
    docker.stop_container(c_id)
    flash('Server successfully stopped.', 'success')
    return redirect(url_for('index'))

@app.route('/start/<c_id>')
def start(c_id):
    docker.start_container(c_id)
    flash('Server successfully started.', 'success')
    return redirect(url_for('index'))

@app.route('/remove/<c_id>')
def remove(c_id):
    docker.remove_container(c_id)
    flash('Server successfully removed.', 'success')
    return redirect(url_for('index'))

@app.route('/add/<dbtype>', methods=['GET', 'POST'])
def add(dbtype):
    if request.method == 'POST':
        name = request.form.get('name')
        ml = request.form.get('memory_limit')
        pf = request.form.get('port_forwarding')
        app.logger.debug('form values : %s %s %s %s' % (name, ml, pf, dbtype))
        container = docker.create_container('mysql')
        app.logger.debug(container)
        flash('Server successfully started.', 'success')
        return redirect(url_for('index'))
    return render_template('add.html', dbtype=dbtype)

@app.route('/pulse/<c_id>')
def pulse(c_id):
    status = docker.test_container(c_id, 'mysql', quiet=True)
    return jsonify({'up': status})

if __name__ == '__main__':
    app.run(host='0.0.0.0')
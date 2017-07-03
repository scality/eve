#!/usr/bin/env python

import os
import subprocess

from celery import Celery
from flask import abort, Flask, jsonify, request, url_for

app = Flask(__name__)

app.config.update(
    CELERY_BROKER_URL='redis://localhost:6379',
    CELERY_RESULT_BACKEND='redis://localhost:6379'
)

def make_celery(app):
    celery = Celery(app.import_name,
                    backend=app.config['CELERY_RESULT_BACKEND'],
                    broker=app.config['CELERY_BROKER_URL'])
    celery.conf.update(app.config)
    TaskBase = celery.Task
    class ContextTask(TaskBase):
        abstract = True
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return TaskBase.__call__(self, *args, **kwargs)
    celery.Task = ContextTask
    return celery

celery = make_celery(app)

@celery.task()
def docker_call(cmd_str):
    retcode = -1
    try:
        cmd = cmd_str.split()
        print('cmd: %s' % cmd)
        ret = subprocess.check_output(cmd, stderr=subprocess.STDOUT)
        retcode = 0
    except subprocess.CalledProcessError as excp:
        ret = excp.output
        retcode = 1
    return {'output': ret, 'retcode': retcode}

@app.route('/status/<task_id>')
def taskstatus(task_id):
    task = docker_call.AsyncResult(task_id)
    response = {'state': task.state}
    if task.state == 'SUCCESS':
        response['output'] = str(task.info.get('output', ''))
        response['retcode'] = str(task.info.get('retcode', 1))
    return jsonify(response)

@app.route('/', methods=['PUT'])
def empty():
    task = docker_call.delay(request.data)
    return jsonify({}), 202, {
        'Location': url_for('taskstatus', task_id=task.id)}

@app.route('/<string:command>', methods=['PUT'])
def docker(command):
    if command == 'run':
        abort(403)
    elif command == 'login':
        abort(403)

    task = docker_call.delay(request.data)

    return jsonify({}), 202, {
        'location': url_for('taskstatus', task_id=task.id)}

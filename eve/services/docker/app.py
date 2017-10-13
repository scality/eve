#!/usr/bin/env python

import json
import subprocess
import traceback

from flask import Flask, jsonify, request, url_for

from celery import Celery
from command import command_factory

app = Flask(__name__)
app.config.update(
    DEBUG=True,
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
def call(target_cmd):
    """Create a task that runs the provided command."""
    retcode = -1
    try:
        ret = subprocess.check_output(target_cmd, stderr=subprocess.STDOUT)
        retcode = 0
    except subprocess.CalledProcessError as excp:
        ret = excp.output
        retcode = 1

    return {'output': ret.decode('utf-8'),
            'retcode': retcode}


@app.route('/status/<task_id>')
def taskstatus(task_id):
    task = call.AsyncResult(task_id)
    response = {'state': task.state}
    if task.state == 'SUCCESS':
        retcode = task.info.get('retcode', 1)
        output = task.info.get('output', u'')
        app.logger.info(u'<{task}> res: {retcode}, output:\n{output}'.format(
            task=task.id,
            retcode=retcode,
            output=output))
        response['output'] = output
        response['retcode'] = retcode
    return jsonify(response)


def bad_request(code, traceback):
    response = jsonify({'traceback': traceback})
    response.status_code = code
    return response


@app.route('/<string:command>', methods=['PUT'])
def docker(command):
    try:
        cmd = command_factory(command)
    except Exception:
        traceback.print_exc()
        app.logger.error(
            'exception occured while looking up: {cmd}'.format(
                cmd=cmd))
        return bad_request(403, traceback.format_exc())

    original_cmd = json.loads(request.form['command'])
    stdin = json.loads(request.form['stdin'])
    try:
        target_cmd = cmd.convert(original_cmd, stdin, request.files)
    except Exception:
        traceback.print_exc()
        app.logger.error(
            'exception occured while converting:\n{ori}'.format(
                ori=' '.join(original_cmd)))
        return bad_request(500, traceback.format_exc())

    task = call.delay(target_cmd)

    app.logger.info('<{task}> ---> {ori}\n<{task}> <--- {conv}'.format(
        task=task.id,
        ori=' '.join(original_cmd),
        conv=' '.join(target_cmd)))

    return jsonify({}), 202, {
        'location': url_for('taskstatus', task_id=task.id)}


@app.route("/healthz", methods=['GET'])
def healthz():
    return 'OK!'

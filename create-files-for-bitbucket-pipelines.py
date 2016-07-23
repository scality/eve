import os

ENV_FILES = [
    ('GIT_CERT_KEY','certs/git/id_rsa'),
    ('MASTER_DOCKER_CERT_CA','certs/docker_master/ca.pem'),
    ('MASTER_DOCKER_CERT_KEY','certs/docker_master/key.pem'),
    ('MASTER_DOCKER_CERT_CERT','certs/docker_master/cert.pem'),
    ('WORKERS_DOCKER_CERT_CA','certs/docker_workers/ca.pem'),
    ('WORKERS_DOCKER_CERT_KEY','certs/docker_workers/key.pem'),
    ('WORKERS_DOCKER_CERT_CERT','certs/docker_workers/cert.pem'),
]

for var_name, filename in ENV_FILES:
    try:
        os.makedirs(os.path.dirname(filename))
    except OSError:
        pass
    with open(filename, 'w') as file_handle:
        content = os.environ[var_name]
        content = content.replace(' RSA PRIVATE KEY-----', '__RSAPRVK__')
        content = content.replace(' CERTIFICATE-----', '__RSACERT__')
        content = content.replace(' ', '\n')
        content = content.replace('__RSAPRVK__', ' RSA PRIVATE KEY-----')
        content = content.replace('__RSACERT__', ' CERTIFICATE-----')
        file_handle.write(content)

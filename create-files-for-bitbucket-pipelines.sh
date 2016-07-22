# git
mkdir -p certs/bitbucket.git_certs
echo "$GIT_CERT_KEY" > certs/git/id_rsa

# Docker Master
MASTER_DOCKER_CERT_PATH=certs/docker_master
mkdir $MASTER_DOCKER_CERT_PATH

echo "$MASTER_DOCKER_CERT_CA" > $MASTER_DOCKER_CERT_PATH/ca.pem
echo "$MASTER_DOCKER_CERT_KEY" > $MASTER_DOCKER_CERT_PATH/key.pem
echo "$MASTER_DOCKER_CERT_CERT" > $MASTER_DOCKER_CERT_PATH/cert.pem

# Docker Workers
WORKERS_DOCKER_CERT_PATH=certs/docker_workers
mkdir "$WORKERS_DOCKER_CERT_PATH"

echo "$WORKERS_DOCKER_CERT_CA" > $WORKERS_DOCKER_CERT_PATH/ca.pem
echo "$WORKERS_DOCKER_CERT_KEY" > $WORKERS_DOCKER_CERT_PATH/key.pem
echo "$WORKERS_DOCKER_CERT_CERT" > $WORKERS_DOCKER_CERT_PATH/cert.pem

# Web SSL
WEB_CERT_PATH=certs/web
mkdir $WEB_CERT_PATH
echo "$WORKERS_CERT" > $WEB_CERT_PATH/devsca_full_bundle.crt
echo "$WORKERS_KEY" > $WEB_CERT_PATH/devsca_com.key
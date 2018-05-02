FROM dldl/sphinx-server

# install eve in container to obtain a version number
RUN apk update && \
    apk upgrade && \
    apk add git
COPY . /opt/eve
RUN pip install --no-deps /opt/eve

COPY ./doc/source /web/
VOLUME ["/web/_build"]

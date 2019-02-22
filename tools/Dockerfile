FROM python:3.6.8-alpine

COPY requirements.txt /tmp/requirements.txt

RUN pip install -r /tmp/requirements.txt

COPY ./eve_api_client ./githost.py ./eve_client.py ./utils.py / 

ENTRYPOINT ["/eve_api_client"]

CMD ["--help"]

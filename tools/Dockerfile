FROM jfloff/alpine-python:3.6-slim

COPY ./eve_api_client ./githost.py ./eve_client.py ./utils.py /
ENTRYPOINT ["/eve_api_client"]

CMD ["--help"]

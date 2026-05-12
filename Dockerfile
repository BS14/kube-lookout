FROM python:3.9-alpine

ADD requirements.txt pyproject.toml /app/

RUN apk update && \
    apk add --no-cache libffi openssl && \
    apk add --no-cache --virtual .build-deps gcc musl-dev libffi-dev openssl-dev && \
    pip install --upgrade pip wheel && \
    pip install -r /app/requirements.txt --ignore-installed six && \
    apk del .build-deps && \
    rm -rf /var/cache/apk/*

ADD kube_lookout/ /app/kube_lookout/
RUN pip install --no-deps /app

ENTRYPOINT ["python3", "-u", "-m", "kube_lookout.main"]

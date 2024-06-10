FROM python:3.9-alpine

# Add requirements.txt
ADD requirements.txt /tmp

# Install necessary packages and dependencies
RUN apk update && \
    apk add --no-cache libffi openssl && \
    apk add --no-cache --virtual .build-deps gcc musl-dev libffi-dev openssl-dev && \
    pip install --upgrade pip && \
    pip install wheel && \
    pip install -r /tmp/requirements.txt --ignore-installed six && \
    apk del .build-deps && \
    rm -rf /var/cache/apk/*

# Add the lookout script
ADD lookout.py /root

# Set the entrypoint
ENTRYPOINT ["python3", "-u", "/root/lookout.py"]

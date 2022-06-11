FROM python:3.10-slim

COPY requirements.txt /tmp/requirements.txt

RUN pip install --no-cache-dir --upgrade pip setuptools \
    && pip install --no-cache-dir -r /tmp/requirements.txt \
    && rm /tmp/requirements.txt

COPY . .

ENTRYPOINT [ "python", "galactory.py" ]

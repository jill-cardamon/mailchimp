FROM --platform=linux/amd64 python:3.7-slim

RUN pip install confluent-kafka

WORKDIR /opt/producer

# COPY requirements.txt /opt/producer/

# RUN pip install --no-cache-dir -r /opt/producer/requirements.txt

# to keep the container running during development
CMD ["tail" "-F" "anything"]
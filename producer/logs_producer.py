import time
import json
import urllib.request
from confluent_kafka import Producer

log_url = "https://raw.githubusercontent.com/elastic/examples/master/Common%20Data%20Formats/nginx_json_logs/nginx_json_logs"
producer = Producer({'bootstrap.servers': 'kafka:9092'})

# delivery report
def delivery_report(err, msg):
    """
    Reports the failure or success of a message delivery.

    Args:
        err (KafkaError): The error that occurred on None on success.

        msg (Message): The message that was produced or failed.
    """
    if err is not None:
        print("Delivery failed for User record {}: {}".format(msg.key(), err))
        return
    print(
        'User record {} successfully produced to {} [{}] at offset {} with value: {}'.format(
            msg.key(), msg.topic(), msg.partition(), msg.offset(), msg.value()
        )
    )

def download_logs():
    url = urllib.request.urlopen(log_url)
    return url

# Push the records to a Kafka topic
def push_update_to_kafka(record, topic):
    producer.produce(
        topic=topic,
        key=None,
        value=record,
        timestamp=3,
        on_delivery=delivery_report,
    )
    producer.flush()

# load file, produce each line to kafka topic
def gen_log_stream():
    logs = download_logs()
    for line in logs:
        try:
            log = json.loads(line)
            entity = json.dumps(log).encode('utf-8')
            time.sleep(15) # for development
            push_update_to_kafka(entity, 'nginx_access_logs')
        except TypeError:
            return

if __name__ == "__main__":
    gen_log_stream()
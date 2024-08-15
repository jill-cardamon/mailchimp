### Data Engineer Technical Assessment

#### Questions to keep in mind:

* What factors were taken into consideration for the pipeline design?
* Does the design accommodate for increase volume and velocity?

#### Instructions:

* Produce the dataset to a message queue using a producer
    * Message Queues: Kafka, Redis, RabbitMQ, etc
    * Producers: Python, Fluentd, Logstash, etc
* Consume data from queue, transform to the data format below, and index the events into OpenSearch cluster.
    * Consumers: Python, Fluentd, Logstash
* Create dashboard (using OpenSearch) of visualizations that are insightful about the dataset.

#### Need:

* docker compose file that will stand up your data pipeline end-to-end
* set of helper scripts that will help you interact with the data pipeline. could do the following:
    * start the data pipeline
    * stop the data pipeline
    * produce the events to the data pipeline
    * monitor the data pipeline
    * give the status of all of the components of the data pipeline
* README that will document how to use the docker compose file and helper scripts
* design document describing your technical solution and an architecture diagram


#### Data format:

```
{
    "time": 1426279439, // epoch time derived from the time field in the event
    "sourcetype": "nginx",
    "index": "nginx",
    "fields": {
        "region": "us-west-1",
        "assetid": "8972349837489237"
    },
    "event": {
        "remote_ip": "93.180.71.3",
        "remote_user": "-",
        "request": "GET /downloads/product_1 HTTP/1.1",
        "response": 304,
        "bytes": 0,
        "referrer": "-",
        "agent": "Debian APT-HTTP/1.3 (0.8.16~exp12ubuntu10.21)"
    } // this should be all of the data from the event itself, minus time
}
```

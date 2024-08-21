# Design Doc: Nginx Access Logs Pipeline

## Overview

This document outlines the design and implementation details of an end-to-end data pipeline for processing and visualizing nginx access metrics. From a high level, the pipeline retrieves bulk logs in JSON format, produces them to a message queue, consumes the data and performs some manipulations, and sends it downstream to a datastore.

Objectives
* Ingestion: Efficiently ingest nginx access logs (in JSON format)
* Data Processing: Transform the log data to adhere to a specified schema
* Indexing: Index the transformed data into Opensearch for visualization
* Scalability: Ensure the pipeline can handle high throughput
* Reliability: Consider fault tolerance and error handling to ensure data integrity

## Architecture

### High-Level Architecture and Data Flow

Our pipeline architecture is as follows (from left to right):
* Producer (Python): Requests access logs from url and generates a stream of log data
* Message Queue (Kafka): The logs are sent to the corresponding Kafka topic. The data is stored in our state.
* Processing (Logstash):
  * Logstash consumes the data from the Kafka topic.
  * The log data is enriched with static fields, parsed, filtered, and mutated to match the data schema. 
  * The enriched and transformed data is indexed into an Opensearch cluster.
* Monitoring: Metrics are pulled by Prometheus and visualized using Grafana.
  * Kafka exporter and JVM exporter are used to collect Kafka metrics.
  * JSON exporter is used to collect Logstash metrics for Prometheus to scrape.

### Component Considerations



### Data Ingestion

#### Source Data

The source data is bulk raw nginx access logs which are in JSON format. Although JSON is semi-structured, the logs followed a structure:
```
{"time": "17/May/2015:08:05:32 +0000", "remote_ip": "93.180.71.3", "remote_user": "-", "request": "GET /downloads/product_1 HTTP/1.1", "response": 304, "bytes": 0, "referrer": "-", "agent": "Debian APT-HTTP/1.3 (0.8.16~exp12ubuntu10.21)"}
```

An early exploratory data analysis revealed the referrer and remote user fields were most empty while the request and response fields showed the same few values. However, there were no even distributions amongst fields (nor composite fields).

A python script uses urllib to retrieve these bulk nginx logs, and the file is parsed (line by line for individual logs) and produced to Kafka. A delivery report documents the success or failure of message delivery.

Python provides an easy to use and versatile environment for read and producing JSON data. Its library support allows for quick integration with Kafka. This section of the pipeline is solely responsible for producing JSON records to a message queue, so there is no need to introduce additional complexity and resource allocation by using a producer like Logstash or Fluentd.


#### Kafka Configuration

Logs are produced to using a single topic approach with no key, leaving Kafka to evenly distribute events between topic partitions. The data is homogenous and serves a unified purpose, so this approach simplifies consumption as all related messages are within the same topic and traffic is not skewed amongst partitions. The exploratory data analysis showed that there was no convenient distribution of records amongst fields (nor composite fields), so a multiple topic or dynamic topic approach would benefit the system if additional sources of logs were included or the use case (like needing to ensure order of processing) encouraged it. 

**Considerations**: Kafka is a reliable and scalable message queue that can handle huge volumes of data. When picking a message queue, it's important to think about a few things: scalability, performance, durability, and delivery guarantees. Compared to other MQs, Kafka has a higher throughput than RabbitMQ and is more durable due to storing on disk (RabbitMQ stores in memory I believe). While this does introduce higher latency, that tradeoff is worth it that monitors logs. In the future, if this system needs to accommodate a larger quantity of data, Kafka can adapt to that better than RabbitMQ can. At the same time, Kafka can ensure ordering of events which could become important for determining the causal relationship between log info. Plus, there's flexibility with Kafka if there is a need for streaming and storage by using KSQL. You can persist messages (which you can do with RabbitMQ as well) for usage as well.

### Data Transformation

The raw logs are manipulated into this format:
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
    }
}
```

#### Logstash Configuration

**Considerations**: Logstash is a data processing pipeline that ingests data from sources, transforms it, and then sends it to storage. It supports a wide range of plugins which allows for extensive customization of the data processing. In addition to its flexibility, Logstash integrates well with Kafka and Opensearch, ensuring smooth data flow. Compared to Fluentd, its performance and resource consumption are high, but this is a worthwhile tradeoff for performance in the case that the pipeline experiences increased volume and/or velocity.

**Pipeline**: Logstash consumes JSON-formatted log entries with decorated events from Kafka for access to metadata. It then filters the data before sinking it to Opensearch using a stream approach as well as to stdout for development and debugging purposes. The pipeline batch size was increased from the default to avoid data loss as Logstash lagged behind.

**Filters**: Logstash uses several mutate filters to remove unnecessary fields, add the status fields (region and assetid), and set the sourcetype and index. The raw JSON events are then parsed for access to their fields. The event time is used for the timestamp metadata (for filtering in Opensearch Dashboards), and ruby code derives epoch time from that event time.

**Error Handling**: A debug field was introduced for the timestamp to ensure that Opensearch visualizations that depended on time-series information worked.  A future improvement could implement conditional checks to filter out or log malformed entries as well as send malformed messages to an index for further analysis.

### Data Storage and Visualization

Data is indexed into Opensearch. Due to their homogenous nature, there is a single nginx index.

While the majority of the transformation happened in Logstash, a few scripted fields were added to Opensearch in order to provide more granular insights into the data such as user-agent  information, request methods and products, and “fingerprint” generation duplicate record counts.

#### Dashboard

Visualizations exist in the `Nginx Access Logs` dashboard. Key metrics like record count, unique remote_ip count, and requests per product give an overview of pipeline performance and request distribution. Composite visualizations provide additional insight into requests and response code distribution over time, most frequent remote_ips, and distribution of response types by request to highlight where traffic and errors might be concentrated concentrated.


### Monitoring

The pipeline is monitored with Prometheus and Grafana to track the health of Kafka, Logstash, and OpenSearch. While Opensearch has a convienient Prometheus plugin, Kafka and Logsearch use exporters in order to maintain a centralized hub. The introduced complexity is a tradeoff for maintainance and alerting.

Kafka metrics are collected by Kafka exporter and JVM exporter.

Logstash metrics are collect by JSON exporter for Prometheus to scrape. These metrics are especially important because they play a crucial role in detecting data loss when compared to Kafka's produced event metrics as well as alerting when resource usage is high.

### Potential Bottlenecks

Bottlenecks arise when 
























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



When designing a pipeline, it's important to think about a few things:
    * reliability, scalability, and maintainability
Everything is about constraints and tradeoffs.
Want to also only include additional complexity when absolutely necessary. Do we need to use something other than python as a producer or consumer?

#### TODO:

* architecture diagram
* docker compose for standing up components
    * producer, message queue, consumer, opensearch
    * kafka, logstash, and opensearch first
* produce dataset onto message queue
* consume data from queue
* transform data into designated format
* sink data into OpenSearch cluster
* choose index
* determine helpful visualizations about the dataset
* create dashboard (use playground: https://playground.opensearch.org/app/home#/)
* monitor the data pipeline
* give status of all components of the pipeline

# Visualizations:
- request distribution by endpoint
- response code distribution
- combination of request and response distribution
- top ip address by request
- something about the top request by most frequent IPs
- volume of requests over time
- distribution of request frequency by IP
- error rate over time
- duplicate records count (not sure how i would get this one tbh)
- response size distribution

curl -X POST -H "osd-xsrf: true" "http://localhost:5601/api/saved_objects/_import?overwrite=true" --form file=@export.ndjson

curl -XPUT 'http://localhost:9200/_all/_settings?preserve_existing=true' -d '{"index.default_pipeline" : "{ 'description': 'This pipeline processes nginx access log data', 'processors': [ { 'fingerprint': { 'on_failure': [ { 'set': { 'field': 'fingerprint_error', 'value': 'failed' } } ] } }, { 'user_agent': { 'field': 'event.agent', 'on_failure': [ { 'set': { 'field': 'user_agent_error', 'value': 'failed' } } ] } }] }"}'

curl -XPUT 'http://localhost:9200/_all/_settings?preserve_existing=true' -H 'Content-Type: application/json' -d '{"index.default_pipeline" : "{'processors': [ { 'fingerprint': { 'on_failure': [ { 'set': { 'field': 'fingerprint_error', 'value': 'failed' } } ] } }, { 'user_agent': { 'field': 'event.agent', 'on_failure': [ { 'set': { 'field': 'user_agent_error', 'value': 'failed' } } ] } }, { 'grok': { 'field': 'event.request', 'patterns': ['%{WORD:method} %{URIPATHPARAM:request_path} HTTP/%{NUMBER:http_version}'], 'on_failure': [ { 'set': { 'field': 'grok_error', 'value': 'failed' } } ] } } ] }"}'

curl -XPUT 'http://localhost:9200/_all/_settings?preserve_existing=true' -d '{"index.default_pipeline" : "{ 'description': 'This pipeline processes nginx access log data', 'processors': [ { 'fingerprint': { 'on_failure': [ { 'set': { 'field': 'fingerprint_error', 'value': 'failed' } } ] } }, { 'user_agent': { 'field': 'event.agent', 'on_failure': [ { 'set': { 'field': 'user_agent_error', 'value': 'failed' } } ] } }, { 'grok': { 'field': 'event.request', 'patterns': ['%{WORD:method} %{URIPATHPARAM:request_path} HTTP/%{NUMBER:http_version}'], 'on_failure': [ { 'set': { 'field': 'grok_error', 'value': 'failed' } } ] } } ] }"}'

curl -X PUT 'http://localhost:9200/_all/_settings?preserve_existing=true' -H 'Content-Type: application/json' -d '{"index.default_pipeline" : "{'processors': [ { 'fingerprint': { 'on_failure': [ { 'set': { 'field': 'fingerprint_error', 'value': 'failed' } } ] } }, { 'user_agent': { 'field': 'event.agent', 'on_failure': [ { 'set': { 'field': 'user_agent_error', 'value': 'failed' } } ] } } ] }"}'

curl -X PUT 'http://localhost:9200/_all/_settings?preserve_existing=true' -H 'Content-Type: application/json' -d '{"index.default_pipeline" : "{'processors': [ { 'grok': { 'field': 'event.request', 'patterns': ['%{WORD:method} %{URIPATHPARAM:request_path} HTTP/%{NUMBER:http_version}'], 'on_failure': [ { 'set': { 'field': 'user_agent_error', 'value': 'failed' } } ] } } ] }"}'

{ 'grok': { 'field': 'event.request', 'patterns': ['%{WORD:method} %{URIPATHPARAM:request_path} HTTP/%{NUMBER:http_version}'], 'on_failure': [ { 'set': { 'field': 'user_agent_error', 'value': 'failed' } } ] } }


PUT _ingest/pipeline/my-pipeline
{
  "description": "This pipeline processes nginx access log data",
  "processors": [
    {
      "fingerprint": {
        "on_failure": [
          {
            "set": {
              "field": "fingerprint_error",
              "value": "failed"
            }
          }
        ]
      }
    },
    {
      "user_agent": {
        "field": "event.agent",
        "on_failure": [
          {
            "set": {
              "field": "user_agent_error",
              "value": "failed"
            }
          }
        ]
      }
    },
    {
      "grok": {
        "field": "event.request",
        "patterns": ["%{WORD:method} %{URIPATHPARAM:request_path} HTTP/%{NUMBER:http_version}"]
      }
    }
  ]
}

import_opensearch_dashboard:
	curl -X POST -H "osd-xsrf: true" "http://localhost:5601/api/saved_objects/_import?overwrite=true" --form file=@export.ndjson

set_default_pipeline_test:
	curl -XPUT "http://localhost:9200/nginx*/_settings" { "index.default_pipeline": "my-pipeline" }

set_default_pipeline:
	curl -XPUT "http://localhost:9200/nginx*/_settings" -H 'Content-Type: application/json' -d '{ "index.default_pipeline": "my-pipeline" }'

set_opensearch_ingest_pipeline:
	curl -XPUT "http://localhost:9200/_ingest/pipeline/my-pipeline" -H 'Content-Type: application/json' -d '{ "processors": [ { "fingerprint": { "on_failure": [ { "set": { "field": "fingerprint_error", "value": "failed" } } ] } }, { "user_agent": { "field": "event.agent", "on_failure": [ { "set": { "field": "user_agent_error", "value": "failed" } } ] } } ] }'

produce:
	docker compose -f docker-compose.produce.yml up -d

#### Data format:

CURRENT REPRESENTATION IN LOGSTASH:
{
    "time" => "1431849934",
    "fields" => {
        "assetid" => "8972349837489237",
        "region" => "us-west-1"
    },

    "message" => "{\"time\": \"17/May/2015:08:05:34 +0000\", \"remote_ip\": \"217.168.17.5\", \"remote_user\": \"-\", \"request\": \"GET /downloads/product_1 HTTP/1.1\", \"response\": 200, \"bytes\": 490, \"referrer\": \"-\", \"agent\": \"Debian APT-HTTP/1.3 (0.8.10.3)\"}",

    "remote_ip" => "217.168.17.5",
    "remote_user" => "-",
    "request" => "GET /downloads/product_1 HTTP/1.1",
    "response" => 200
    "bytes" => 490,
    "referrer" => "-",
    "agent" => "Debian APT-HTTP/1.3 (0.8.10.3)",
}


{
    "bytes" => 337,
    "message" => "{\"time\": \"17/May/2015:08:05:02 +0000\", \"remote_ip\": \"217.168.17.5\", \"remote_user\": \"-\", \"request\": \"GET /downloads/product_2 HTTP/1.1\", \"response\": 404, \"bytes\": 337, \"referrer\": \"-\", \"agent\": \"Debian APT-HTTP/1.3 (0.8.10.3)\"}",
    "event" => {},
    "remote_ip" => "217.168.17.5",
    "response" => 404,
    "referrer" => "-",
    "fields" => {
        "region" => "us-west-1",
        "assetid" => "8972349837489237"
    },
    "agent" => "Debian APT-HTTP/1.3 (0.8.10.3)",
    "time" => "1431849902",
    "request" => "GET /downloads/product_2 HTTP/1.1",
    "remote_user" => "-"
}


{
2024-08-16 11:38:37            "tags" => [
2024-08-16 11:38:37         [0] "_rubyexception"
2024-08-16 11:38:37     ],
2024-08-16 11:38:37         "message" => "{\"time\": \"17/May/2015:08:05:34 +0000\", \"remote_ip\": \"217.168.17.5\", \"remote_user\": \"-\", \"request\": \"GET /downloads/product_1 HTTP/1.1\", \"response\": 200, \"bytes\": 490, \"referrer\": \"-\", \"agent\": \"Debian APT-HTTP/1.3 (0.8.10.3)\"}",
2024-08-16 11:38:37           "event" => {},
2024-08-16 11:38:37     "parsed_json" => {
2024-08-16 11:38:37            "referrer" => "-",
2024-08-16 11:38:37               "bytes" => 490,
2024-08-16 11:38:37         "remote_user" => "-",
2024-08-16 11:38:37           "remote_ip" => "217.168.17.5",
2024-08-16 11:38:37                "time" => "17/May/2015:08:05:34 +0000",
2024-08-16 11:38:37            "response" => 200,
2024-08-16 11:38:37               "agent" => "Debian APT-HTTP/1.3 (0.8.10.3)",
2024-08-16 11:38:37             "request" => "GET /downloads/product_1 HTTP/1.1"
2024-08-16 11:38:37     },
2024-08-16 11:38:37          "fields" => {
2024-08-16 11:38:37          "region" => "us-west-1",
2024-08-16 11:38:37         "assetid" => "8972349837489237"
2024-08-16 11:38:37     }
2024-08-16 11:38:37 }

{
2024-08-16 11:41:24       "event" => {
2024-08-16 11:41:24            "response" => 200,
2024-08-16 11:41:24           "remote_ip" => "217.168.17.5",
2024-08-16 11:41:24         "remote_user" => "-",
2024-08-16 11:41:24               "bytes" => 490,
2024-08-16 11:41:24            "referrer" => "-",
2024-08-16 11:41:24               "agent" => "Debian APT-HTTP/1.3 (0.8.10.3)",
2024-08-16 11:41:24                "time" => "17/May/2015:08:05:34 +0000",
2024-08-16 11:41:24             "request" => "GET /downloads/product_1 HTTP/1.1"
2024-08-16 11:41:24     },
2024-08-16 11:41:24        "tags" => [
2024-08-16 11:41:24         [0] "_rubyexception"
2024-08-16 11:41:24     ],
2024-08-16 11:41:24     "message" => "{\"time\": \"17/May/2015:08:05:34 +0000\", \"remote_ip\": \"217.168.17.5\", \"remote_user\": \"-\", \"request\": \"GET /downloads/product_1 HTTP/1.1\", \"response\": 200, \"bytes\": 490, \"referrer\": \"-\", \"agent\": \"Debian APT-HTTP/1.3 (0.8.10.3)\"}",
2024-08-16 11:41:24      "fields" => {
2024-08-16 11:41:24         "assetid" => "8972349837489237",
2024-08-16 11:41:24          "region" => "us-west-1"
2024-08-16 11:41:24     }
2024-08-16 11:41:24 }

{
2024-08-16 11:48:53     "message" => "{\"time\": \"17/May/2015:08:05:09 +0000\", \"remote_ip\": \"217.168.17.5\", \"remote_user\": \"-\", \"request\": \"GET /downloads/product_2 HTTP/1.1\", \"response\": 200, \"bytes\": 490, \"referrer\": \"-\", \"agent\": \"Debian APT-HTTP/1.3 (0.8.10.3)\"}",
2024-08-16 11:48:53      "fields" => {
2024-08-16 11:48:53         "assetid" => "8972349837489237",
2024-08-16 11:48:53          "region" => "us-west-1"
2024-08-16 11:48:53     },
2024-08-16 11:48:53       "event" => {
2024-08-16 11:48:53           "remote_ip" => "217.168.17.5",
2024-08-16 11:48:53             "request" => "GET /downloads/product_2 HTTP/1.1",
2024-08-16 11:48:53               "bytes" => 490,
2024-08-16 11:48:53            "response" => 200,
2024-08-16 11:48:53            "referrer" => "-",
2024-08-16 11:48:53         "remote_user" => "-",
2024-08-16 11:48:53               "agent" => "Debian APT-HTTP/1.3 (0.8.10.3)"
2024-08-16 11:48:53     },
2024-08-16 11:48:53        "time" => "1431849909"
2024-08-16 11:48:53 }

{
2024-08-16 11:53:59      "event" => {
2024-08-16 11:53:59         "remote_user" => "-",
2024-08-16 11:53:59             "request" => "GET /downloads/product_1 HTTP/1.1",
2024-08-16 11:53:59               "bytes" => 0,
2024-08-16 11:53:59            "response" => 304,
2024-08-16 11:53:59            "referrer" => "-",
2024-08-16 11:53:59               "agent" => "Debian APT-HTTP/1.3 (0.8.16~exp12ubuntu10.21)",
2024-08-16 11:53:59           "remote_ip" => "93.180.71.3"
2024-08-16 11:53:59     },
2024-08-16 11:53:59     "fields" => {
2024-08-16 11:53:59         "assetid" => "8972349837489237",
2024-08-16 11:53:59          "region" => "us-west-1"
2024-08-16 11:53:59     },
2024-08-16 11:53:59       "time" => "1431849927"
2024-08-16 11:53:59 }












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
    }
}
```


- get in shape for for initial commit
- create github repo
- transform data into the desired format
- create dashboard visualizations

#### Tools

Producer: 
* Plus, I wanted to learn a new tool!

Message Queue: Kafka
ORDERING IS IMPORTANT. When analyzing logs, for debugging or incident investigation, the order of log entries is crucial to understanding the sequence of events that led to an issue.
Consistency: The order of processing ensures that data reflects the correct sequence of real-world events, maintaining consistency and accuracy.
Causality: Correct order processing preserves the causal relationships between events, which is crucial for understanding and interpreting system behavior.
State Integrity: In systems that rely on maintaining state, processing data in the correct order is essential to avoid corruption or incorrect state.

* When picking a message queue, it's important to think about a few things:
    * scalability, performance, persistence and durability, delivery guarantees, integration, fault tolerance, availability, latency

* Kafka has a higher throughput than RabbitMQ and is more durable due to storing on disk (RabbitMQ stores in memory I believe). While this does introduce higher latency, that tradeoff is worth it in my opinion for a pipeline that monitors access logs. In the future, if this system needs to accomodate a larger quantity of data, then Kafka can adapt to that better than RabbitMQ can.
* There's flexibility with Kafka if you want to do other things by using KSQL. You can persist messages (which you can do with RabbitMQ as well) for usage as well.

Partitioning:
It's important to ensure an even distribution of data across Kafka partitions. So, we need to carefully choose the topic and partitioning strategy while considering the spread of the data.
For the topic: Given that the data is related (HTTP requests and responses), it makes sense to use a single topic (`nginx_access_logs`) to simplify processing and avoid topic proliferation.


How to handle duplicate logs?

At what scale, could things break?
When would you swap out components? and for what reasons?
How would you make it faster?
Respond to questions you don't know with curiousity! Learn where you don't know.
- example: if asked about multi-threading, say i dont know wasnt aware. what could be the problem that arises there?


The OpenSearch output plugin can store both time series datasets (such as logs, events, and metrics) and non-time series data in OpenSearch. The data stream is recommended to index time series datasets (such as logs, metrics, and events) into OpenSearch.

<!-- Initially, I did XYZ. but after some monitoring, I noticed 123. -->

time           22467
remote_ip       2660
remote_user        1
request            5
response         NaN
bytes            NaN
referrer           8
agent            136



# Testing, auto formatting, type checks, & Lint checks

# ci: isort format type lint

# Run end-to-end
# run:
# 	down up sleep ci run-job

# Monitoring
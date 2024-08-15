FROM docker.elastic.co/logstash/logstash:8.9.2
RUN logstash-plugin install --version 7.1.1 logstash-integration-aws
RUN logstash-plugin install --version 2.0.2 logstash-output-opensearch
# Mailchimp Data Engineer Technical Assessment

Code for a Mailchimp craft demo

## Project

The purpose of this exercise is to demonstrate technical abilities in setting up an end-to-end data pipeline.

Our objectives are:
 1. Produce the given dataset to a message queue.
 2. Consume the data produced in step 1 from the message queue, manipulate it into a given format, and index the events into an Opensearch cluster.
 3. Create an Opensearch dashboard using the indexed data.

## Run locally

### Prerequisites

To run the code, you'll need the following:

1. [git](https://git-scm.com/book/en/v2/Getting-Started-Installing-Git)
2. [Docker](https://docs.docker.com/engine/install/) with at least 4GB of RAM and [Docker Compose](https://docs.docker.com/compose/install/) v1.27.0 or later

## Run the job

Clone the job (via terminal) as shown below:

```bash
git clone https://github.com/jill-cardamon/mailchimp.git
cd mailchimp
```

If using a public assess token, use:
```bash
git clone https://<username>:<token>@github.com/jill-cardamon/mailchimp.gitcd mailchimp
cd mailchimp
```

Create an `.env` file in the root of this project to store the following credentials:

```
OPENSEARCH_INITIAL_ADMIN_PASSWORD=YOUR_OPENSEARCH_PASSWORD_HERE
GF_SECURITY_ADMIN_PASSWORD=YOUR_GRAFANA_PASSWORD_HERE
```

Now, spin up the pipeline and run the job:
```
make run # restart all containers and start the job
```
This command will build the necessary custom Docker images, spin up the containers, set up our monitoring, start producing data, and open Opensearch Dashboards.

1. **Opensearch Dashboards**: Gain insights about the data. The `make run` command will open the dashboard or go to http://localhost:5601/app/dashboards#/. Select the `Nginx Access Logs` board to view key insights about the data. Use the calendar icon on the top right to set a date range from May 17, 2015 to June 5, 2015.

2. **Prometheus**: Open http://localhost:9090 or run `make prom`. Click on Status -> Targets to see the status of metrics endpoints. Data will start to appear in Grafana once an endpoint has an `UP` state.

3. **Grafana**: Visualize system metrics with Grafana, use the `make monitor` command or go to http://localhost:3000 via your browser (username: admin, password:YOUR_GRAFANA_PASSWORD_HERE). Click on Dashboards -> Browse and select a component to view its metrics.

**Note**: Checkout `Makefile` to see how/what commands are run. Use `make down` to spin down the containers.

## Check Component Health

We can check component health and status by viewing system metrics with Grafana (as described above) and container status using `make status`.

## Check output

Once we start the job, it will run asynchronously. We can check Opensearch Dashboards and Grafana to see our running job.

We can check the output of our job by looking at the Opensearch Dashboards data explorer (http://localhost:5601/app/data-explorer/discover#). 

**Note**: You can interact with Opensearch Search via the command line using cURL. Make sure to format the command like `make import_opensearch_dashboard`. 

## Tear down

Use `make down` to spin down the containers and their corresponding volumes.

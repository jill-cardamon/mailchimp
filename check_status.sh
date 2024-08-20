#!/bin/bash

docker ps -a --format "table {{.Names}}\t{{.ID}}\t{{.RunningFor}}\t{{.Status}}"
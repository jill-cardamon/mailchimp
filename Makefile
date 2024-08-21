up:
	docker-compose up -d

down:
	docker-compose down -v

import_opensearch_dashboard:
	curl -X POST -H "osd-xsrf: true" "http://localhost:5601/api/saved_objects/_import?overwrite=true" --form file=@export.ndjson

sleep:
	sleep 120

viz:
	open http://localhost:5601/app/dashboards#/

run: down up sleep import_opensearch_dashboard viz

status:
	./check_status.sh

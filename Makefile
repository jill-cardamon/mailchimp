up:
	docker-compose up --build -d

down:
	docker-compose down -v

status:
	./check_status.sh

sleep:
	sleep 20
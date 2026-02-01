.PHONY: build up down logs restart clean

# Build containers
build:
	docker-compose build

# Start containers
up:
	docker-compose up -d

# Start with logs
up-logs:
	docker-compose up

# Stop containers
down:
	docker-compose down

# View logs
logs:
	docker-compose logs -f

# Restart containers
restart:
	docker-compose restart

# Clean everything (containers, volumes, images)
clean:
	docker-compose down -v
	docker system prune -f

# Rebuild from scratch
rebuild:
	docker-compose down -v
	docker-compose build --no-cache
	docker-compose up -d

# Check status
status:
	docker-compose ps
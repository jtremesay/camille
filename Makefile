all: run

run: build
	docker compose --env-file .env up

build:
	docker build -t killruana/camille:main .

.PHONY: all run build
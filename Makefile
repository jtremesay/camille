IMAGE_NAME ?= killruana/camille:main

all:

image:
	docker build -t $(IMAGE_NAME) .

.PHONY: all image
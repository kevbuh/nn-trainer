VERSION=v4
DOCKERUSER=kebu1560

all: 
	make build 
	make push

build:
	docker build -t test-worker-image-72:latest .

push:
	docker tag test-worker-image-72 $(DOCKERUSER)/test-worker-image-72:$(VERSION)
	docker push $(DOCKERUSER)/test-worker-image-72:$(VERSION)
	docker tag test-worker-image-72 $(DOCKERUSER)/test-worker-image-72:latest
	docker push $(DOCKERUSER)/test-worker-image-72:latest
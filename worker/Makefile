VERSION=v4
DOCKERUSER=kebu1560

all: 
	make build 
	make push

build:
	docker build -t test-worker-image-60:latest .

push:
	docker tag test-worker-image-60 $(DOCKERUSER)/test-worker-image-60:$(VERSION)
	docker push $(DOCKERUSER)/test-worker-image-60:$(VERSION)
	docker tag test-worker-image-60 $(DOCKERUSER)/test-worker-image-60:latest
	docker push $(DOCKERUSER)/test-worker-image-60:latest
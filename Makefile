IMAGE := bnay14/kube-notify
RELEASE := 1.0.0

test:
	pytest

image:
	docker build -t $(IMAGE) .

push-image:
	docker build -t $(IMAGE):$(RELEASE) . 
	docker push $(IMAGE):$(RELEASE)

.PHONY: image push-image test

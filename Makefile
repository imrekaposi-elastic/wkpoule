# Monorepo image builds — each target uses ONLY its service directory as context.
# Usage:
#   make build-all
#   REGISTRY=image-registry.openshift-image-registry.svc:5000/wkpoule-prd make push-all
#
# OpenShift: prefer BuildConfig contextDir (see openshift/examples/) or Tekton cloning the repo once.

IMAGE_API ?= wkpoule-api:latest
IMAGE_FRONTEND ?= wkpoule-frontend:latest

.PHONY: build-api build-frontend build-all push-api push-frontend push-all

build-api:
	docker build -t $(IMAGE_API) -f backend/Dockerfile backend

build-frontend:
	docker build -t $(IMAGE_FRONTEND) -f frontend/Dockerfile frontend

build-all: build-api build-frontend

push-api:
	test -n "$(REGISTRY)" || (echo "Set REGISTRY, e.g. \$$(oc registry info --public=false)/wkpoule-prd" && exit 1)
	docker tag $(IMAGE_API) $(REGISTRY)/wkpoule-api:latest
	docker push $(REGISTRY)/wkpoule-api:latest

push-frontend:
	test -n "$(REGISTRY)" || (echo "Set REGISTRY" && exit 1)
	docker tag $(IMAGE_FRONTEND) $(REGISTRY)/wkpoule-frontend:latest
	docker push $(REGISTRY)/wkpoule-frontend:latest

push-all: push-api push-frontend

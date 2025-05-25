# REGISTRY = apecloud-registry.cn-zhangjiakou.cr.aliyuncs.com
REGISTRY = docker.io
IMG = apecloud/aperag-frontend
TAG ?= latest
PLATFORMS ?= linux/arm64,linux/amd64
BUILDX_NAME = ape-buildx

.PHONY: all
all: docker-build

## build assets
.PHONY: build-assets
build-assets:
	BASE_PATH=/web/ yarn build

# buildx setup
.PHONY: docker-buildx-setup
docker-buildx-setup:
	@if ! docker buildx ls | grep -q "$(BUILDX_NAME)"; then \
		docker buildx create --name $(BUILDX_NAME) --use; \
	fi
	docker buildx use $(BUILDX_NAME)
	docker buildx inspect

# build docker
.PHONY: docker-build
docker-build: build-assets docker-buildx-setup
	docker buildx build \
		--platform=$(PLATFORMS) \
		-f Dockerfile \
		--push \
		-t ${REGISTRY}/$(IMG):$(TAG) .
	docker buildx rm $(BUILDX_NAME)

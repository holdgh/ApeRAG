# Image URL to use all building/pushing image targets
VERSION ?= latest
IMG = apecloud/aperag-console

ALPINE_IMAGE = node:18.15.0-alpine3.16
PLATFORMS ?= linux/arm64,linux/amd64
ENVFILE = ./.env

.PHONY: build-assets
build-assets: ## build assets
	yarn build

.PHONY: docker-build
docker-build: ## build apelcoud docker image.
	$(MAKE) build-assets
	docker buildx create --name project-v3-builder --buildkitd-flags '--allow-insecure-entitlement network.host'
	docker buildx build --network=host --platform=${PLATFORMS} -f Dockerfile --push -t ${IMG}:${VERSION} .
	docker buildx rm project-v3-builder
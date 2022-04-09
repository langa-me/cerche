VERSION ?= $(shell cat setup.py | grep version | cut -d '"' -f 2)
GCLOUD_PROJECT:=$(shell gcloud config list --format 'value(core.project)' 2>/dev/null)
NAME ?= search-engine

ifeq ($(GCLOUD_PROJECT),langame-dev)
$(info "Using develoment configuration")
REGISTRY ?= 5306t2h8.gra7.container-registry.ovh.net/dev/${NAME}
else
$(info "Using production configuration")
REGISTRY ?= 5306t2h8.gra7.container-registry.ovh.net/prod/${NAME}
endif

prod: ## Set the GCP project to prod
	gcloud config set project langame-86ac4

dev: ## Set the GCP project to dev
	gcloud config set project langame-dev


docker/build: ## [Local development] build the docker image
	docker buildx build -t ${REGISTRY}:${VERSION} -t ${REGISTRY}:latest --platform linux/amd64 . -f ./Dockerfile

docker/run: docker/build ## [Local development] run the docker container
	docker run ${REGISTRY}:latest

docker/push: docker/build ## [Local development] push the docker image to GCR
	docker push ${REGISTRY}:${VERSION}
	docker push ${REGISTRY}:latest

bare/install: ## [Local development] Upgrade pip, install requirements, install package.
	(\
		python3 -m virtualenv env; \
		. env/bin/activate; \
		python3 -m pip install -U pip; \
		python3 -m pip install -e .; \
		python3 -m pip install -r requirements-test.txt; \
	)

bare/run: ## [Local development] run the main entrypoint
	python3 $(shell pwd)/ss2.py serve --host "0.0.0.0:8082"

clean:
	rm -rf env .pytest_cache *.egg-info **/*__pycache__

release:
	@VERSION=$$(cat setup.py | grep version | cut -d '"' -f 2); \
	echo "Releasing version $$VERSION"; \
	git add .; \
	read -p "Commit content:" COMMIT; \
	echo "Committing '$$VERSION: $$COMMIT'"; \
	git commit -m "$$VERSION: $$COMMIT"; \
	git push origin main; \
	git tag v$$VERSION; \
	git push origin v$$VERSION
	echo "Done, check https://github.com/langa-me/search-server/actions"


.PHONY: help

help: # Run `make help` to get help on the make commands
	@grep -E '^[0-9a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

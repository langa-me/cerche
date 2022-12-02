VERSION ?= $(shell cat setup.py | grep version | cut -d '"' -f 2)
GCLOUD_PROJECT:=$(shell gcloud config list --format 'value(core.project)' 2>/dev/null)
NAME ?= cerche

GOOGLE_SEARCH_CX := $(shell cat .env | grep -w GOOGLE_SEARCH_CX | cut -d "=" -f 2)
GOOGLE_SEARCH_KEY := $(shell cat .env | grep -w GOOGLE_SEARCH_KEY | cut -d "=" -f 2)
PROD_PROJECT_ID := $(shell cat .env | grep -w PROD_PROJECT_ID | cut -d "=" -f 2)
DEV_PROJECT_ID := $(shell cat .env | grep -w DEV_PROJECT_ID | cut -d "=" -f 2)
DATASET_URL := $(shell cat .env | grep -w DATASET_URL | cut -d "=" -f 2)

ifeq ($(GCLOUD_PROJECT),$(DEV_PROJECT_ID))
$(info "Using develoment configuration")
REGISTRY ?= $(shell cat .env | grep -w DEV_REGISTRY | cut -d "=" -f 2)/${NAME}
else
$(info "Using production configuration")
REGISTRY ?= $(shell cat .env | grep -w PROD_REGISTRY | cut -d "=" -f 2)/${NAME}
endif

prod: ## Set the GCP project to prod
	gcloud config set project ${PROD_PROJECT_ID}

dev: ## Set the GCP project to dev
	gcloud config set project ${DEV_PROJECT_ID}


docker/build: ## [Local development] build the docker image
	docker buildx build -t ${REGISTRY}:${VERSION} -t ${REGISTRY}:latest --platform linux/amd64 . -f ./Dockerfile

docker/run: docker/build ## [Local development] run the docker container
	docker run --rm --name search -p 8081:8081 ${REGISTRY}:latest serve --host "0.0.0.0:8081"

docker/run/hub:
	docker run --rm --name search -p 8081:8081 langameai/cerche:latest serve --host "0.0.0.0:8081"

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
	cerche serve --host "0.0.0.0:8081"

bare/run/test: ## [Local development] run the main entrypoint with official google
	cerche test_server --host "0.0.0.0:8081" \
		--query copywriting \
		--n 3

bare/run/google_official: ## [Local development] run the main entrypoint with official google
	cerche serve --host "0.0.0.0:8081" \
		--use_official_google_api True \
		--google_search_key ${GOOGLE_SEARCH_KEY} \
		--google_search_cx ${GOOGLE_SEARCH_CX}

bare/run/use_dataset_urls: ## [Local development]
	cerche serve --host "0.0.0.0:8081" \
		--use_official_google_api True \
		--google_search_key ${GOOGLE_SEARCH_KEY} \
		--google_search_cx ${GOOGLE_SEARCH_CX} \
		--use_dataset_urls ${DATASET_URL}



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
	git tag $$VERSION; \
	git push origin $$VERSION
	@echo "Done, check https://github.com/langa-me/cerche/actions"


.PHONY: help

help: # Run `make help` to get help on the make commands
	@grep -E '^[0-9a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

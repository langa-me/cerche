REGISTRY ?= 5306t2h8.gra7.container-registry.ovh.net/$(shell cat .env | grep OVH_PROJECT_ID | cut -d '=' -f 2)/search-server
VERSION ?= $(shell cat setup.py | grep version | cut -d '"' -f 2)
GCLOUD_PROJECT:=$(shell gcloud config list --format 'value(core.project)' 2>/dev/null)

docker/build: ## [Local development] build the docker image
	docker build -t ${REGISTRY}:${VERSION} . -f ./Dockerfile
	docker build -t ${REGISTRY}:latest . -f ./Dockerfile

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


ops/prod: ## Set the GCP project to prod
	@gcloud config set project langame-86ac4 2>/dev/null
	@sed -i 's/OVH_PROJECT_ID=.*/OVH_PROJECT_ID="prod"/' .env
	@echo "Configured GCP project, OVHCloud project and k8s"

ops/dev: ## Set the GCP project to dev
	@gcloud config set project langame-dev 2>/dev/null
	@sed -i 's/OVH_PROJECT_ID=.*/OVH_PROJECT_ID="dev"/' .env
	@echo "Configured GCP project, OVHCloud project and k8s"



ops/lint: ## [Local development] Run pylint to check code style.
	@echo "Linting"
	env/bin/python3 -m pylint ava

ops/clean:
	rm -rf env .pytest_cache *.egg-info **/*__pycache__

ops/release:
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

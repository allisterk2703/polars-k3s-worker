IMAGE   := lester2703/polars-k3s-worker:latest
SEL     := app=polars-ml-pipeline
CTX_K3S := k3s-mbp-rpi
CTX_ORB := orbstack

.PHONY: prepare split build push deploy delete redeploy status logs download use-k3s use-orbstack

MAKEFLAGS += --silent

help: ## Show this help message
	echo "Available commands:"
	grep -E '^[a-zA-Z0-9_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  🔹 \033[36m%-20s\033[0m %s\n", $$1, $$2}'

download: ## Download the raw dataset (runs download.sh)
	bash scripts/download.sh

prepare: ## Convert raw data to Parquet (prepare.py)
	python scripts/prepare.py

split: ## Split Parquet into 32 partitions and upload to MinIO (split.py)
	python scripts/split.py

build: ## Build the Docker image
	docker build -t $(IMAGE) .

push: ## Login to Docker Hub and push the image
	docker login
	docker push $(IMAGE)

deploy: ## Apply job.yaml
	kubectl apply -f job.yaml

delete: ## Delete the Job (ignore if not found)
	kubectl delete job polars-ml-pipeline --ignore-not-found

redeploy: delete deploy ## Delete and re-deploy both Jobs

status: ## Show Job completions and pod status
	kubectl get job polars-ml-pipeline
	@echo ""
	kubectl get pods -l $(SEL) -o wide

logs: ## Print logs of all worker pods
	@for pod in $$(kubectl get pods -l $(SEL) -o jsonpath='{.items[*].metadata.name}'); do \
		echo "=== $$pod ==="; \
		kubectl logs $$pod; \
		echo ""; \
	done

use-k3s: ## Switch kubectl context to k3s-mbp-rpi
	kubectl config use-context $(CTX_K3S)

use-orbstack: ## Switch kubectl context to orbstack
	kubectl config use-context $(CTX_ORB)

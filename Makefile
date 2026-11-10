SHELL := /bin/bash
unexport VIRTUAL_ENV
export JSII_SILENCE_WARNING_UNTESTED_NODE_VERSION := 1
export AWS_REGION ?= us-east-1
export CDK_DEFAULT_REGION ?= $(AWS_REGION)
STACK := WhiskeyAgentStack
OUTPUTS := cdk-outputs.json
PIP_LINUX := --python-platform aarch64-manylinux2014 --python-version 3.14 --only-binary=:all: --quiet

.PHONY: dev format format-fix lint pre-commit build-agent build-chat build-ui build deploy deploy-agent kb-sync chat ui-dev ui-fixtures test e2e destroy clean-logs synth clean observability

dev:
	uv sync
	-uv run pre-commit install  # needs a git repo
	cd ui && npm ci

format:
	uv run ruff check . --fix

format-fix:
	uv run ruff format .

lint: format format-fix

pre-commit:
	uv run pre-commit run -a --show-diff-on-failure

build-agent:
	rm -rf build/agent
	mkdir -p build/agent
	rsync -a --exclude '__pycache__' --exclude 'requirements.txt' agent/ build/agent/
	uv pip install -r agent/requirements.txt --target build/agent $(PIP_LINUX)

build-chat:
	rm -rf build/chat
	mkdir -p build/chat
	cp service/chat/*.py build/chat/
	uv pip install aws-lambda-powertools==3.40.0 'pydantic>=2.14' 'boto3>=1.43' --target build/chat $(PIP_LINUX)

build-ui:
	cd ui && npm run build

build: build-agent build-chat build-ui

synth: build
	uv run cdk synth --quiet

deploy: build
	uv run cdk deploy $(STACK) --require-approval never --outputs-file $(OUTPUTS)
	$(MAKE) kb-sync

deploy-agent: build-agent build-chat
	uv run cdk deploy $(STACK) --require-approval never --outputs-file $(OUTPUTS)

kb-sync:
	uv run scripts/kb_sync.py

chat:
	uv run scripts/chat_cli.py

ui-dev:
	cd ui && VITE_API_URL=$$(jq -r .$(STACK).ApiUrl ../$(OUTPUTS)) npm run dev

ui-fixtures:
	cd ui && VITE_USE_FIXTURES=true npm run dev

test:
	uv run pytest tests/unit -q

e2e:
	DEEPEVAL_TELEMETRY_OPT_OUT=YES uv run pytest tests/e2e -v -s -p no:cacheprovider --rootdir tests/e2e -W ignore::DeprecationWarning -W ignore::SyntaxWarning

destroy:
	uv run cdk destroy $(STACK) --force
	$(MAKE) clean-logs

observability:
	uv run scripts/enable_observability.py

clean-logs:
	uv run scripts/clean_logs.py

clean:
	rm -rf build/agent build/chat build/kb cdk.out ui/dist

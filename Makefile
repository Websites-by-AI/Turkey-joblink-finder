PY?=python3
run: ; $(PY) -m joblink.cli demo
ingest: ; $(PY) -m joblink.cli ingest --source eleman_net --source cvyolla
test: ; $(PY) -m pytest -q
lint: ; $(PY) -m ruff check joblink tests || true
sites: ; $(PY) -m joblink.cli sites
check: ; $(PY) -m joblink.cli check --source eleman_net --parse --no-cache
worker-dev: ; cd worker && wrangler dev
worker-deploy: ; cd worker && wrangler deploy
clean: ; rm -rf data/cache data/joblink.sqlite3
.PHONY: run test lint sites check ingest worker-dev worker-deploy clean

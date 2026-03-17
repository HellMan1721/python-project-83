install:
	uv sync

dev:
	uv run flask --debug --app page_analyzer:app run

PORT ?= 8000
start:
	uv run gunicorn -w 5 -b 0.0.0.0:$(PORT) 'page_analyzer:app'

render-start:
	gunicorn -w 5 -b 0.0.0.0:$(PORT) 'page_analyzer:app'

build:
	./build.sh

lint:
	uv run ruff check --fix .

format:
	uv run ruff format .

check:
	uv run ruff check .

push:
	git add . & git commit -m 'thangs' & git push
	
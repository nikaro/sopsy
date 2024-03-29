all:

lock:
	rye lock --all-features --update-all

sync:
	rye sync --all-features --no-lock || rye sync --all-features --no-lock --force

lint:
	rye run lint
	pre-commit run --all-files

test:
	rye run test

build:
	rye build

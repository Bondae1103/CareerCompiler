.PHONY: lint typecheck test all

PYTHON = .venv/Scripts/python.exe
RUFF = .venv/Scripts/ruff.exe
MYPY = .venv/Scripts/mypy.exe
PYTEST = .venv/Scripts/pytest.exe

all: lint typecheck test

lint:
	$(RUFF) check .

typecheck:
	$(MYPY) careercompiler tests

test:
	$(PYTEST)

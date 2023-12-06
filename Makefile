-include .env
export

PYTHON = python3

venv:
	$(PYTHON) -m venv .venv && \
	source .venv/bin/activate && \
	make reqs
	@echo "========================"
	@echo "Virtual environment successfully created. To activate the venv:"
	@echo "	\033[0;32msource .venv/bin/activate"

reqs:
	$(PYTHON) -m pip install -r requirements.txt
	$(PYTHON) -m spacy download en_core_web_lg

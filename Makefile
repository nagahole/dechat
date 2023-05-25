# INTENDED FOR MACOS - WILL OPEN SERVER / CLIENT IN TERMINAL
# ONLY IF RUN ON MACOS

PYTHON = python3

SERVER_FLAGS = --auto-retry
CLIENT_FLAGS = --ui

TEST_CASE_DIR = test
TESTCASES = base_tests

TESTCASE_FILES = ${patsubst %, ${TEST_CASE_DIR}/%.py, ${TESTCASES}}

server: server.py
	$(eval DIR := $(shell pwd))
	@osascript \
	-e 'tell app "Terminal"' \
		-e 'do script "cd $(DIR) && $(PYTHON) $^ $(SERVER_FLAGS)"' \
		-e 'activate' \
	-e 'end tell'

	@osascript \
	-e 'tell app "Terminal"' \
		-e 'do script "cd $(DIR) && $(PYTHON) $^ localhost 9999 $(SERVER_FLAGS)"' \
		-e 'activate' \
	-e 'end tell'

s: server.py
	@$(PYTHON) $^ $(SERVER_FLAGS)

c: client.py
	@$(PYTHON) $^ $(CLIENT_FLAGS)

push:
	@git push git.edstem.org:challenge/85943/assignment-2-dechat
	@git push https://github.com/nagahole/dechat

run_tests:
	@for test in ${TESTCASE_FILES} ; do \
		$(PYTHON) $$test ; \
	done

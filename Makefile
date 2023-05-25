# INTENDED FOR MACOS - WILL OPEN SERVER / CLIENT IN TERMINAL
# ONLY IF RUN ON MACOS

SERVER_FLAGS = --auto-retry
CLIENT_FLAGS = --ui

all: s

client: client.py
	$(eval DIR := $(shell pwd))
	@osascript \
	-e 'tell app "Terminal"' \
		-e 'do script "cd $(DIR) && python3 $^ "' \
		-e 'activate' \
	-e 'end tell'

server: server.py
	$(eval DIR := $(shell pwd))
	@osascript \
	-e 'tell app "Terminal"' \
		-e 'do script "cd $(DIR) && python3 $^ $(SERVER_FLAGS)"' \
		-e 'activate' \
	-e 'end tell'

	@osascript \
	-e 'tell app "Terminal"' \
		-e 'do script "cd $(DIR) && python3 $^ localhost 9999 $(SERVER_FLAGS)"' \
		-e 'activate' \
	-e 'end tell'

both:
	$(eval DIR := $(shell pwd))
	@osascript \
	-e 'tell app "Terminal"' \
		-e 'do script "cd $(DIR) && make server && make client && exit"' \
	-e 'end tell'

s: server.py
	@python3 $^

c: client.py
	@python3 $^ $(CLIENT_FLAGS)

push:
	@git push git.edstem.org:challenge/85943/assignment-2-dechat
	@git push https://github.com/nagahole/dechat

run_tests:
	@python3 testing/base_tests.py

# INTENDED FOR MACOS - WILL OPEN SERVER / CLIENT IN TERMINAL
# ONLY IF RUN ON MACOS

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
		-e 'do script "cd $(DIR) && python3 $^ "' \
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
	@python3 $^

push:
	@git push git.edstem.org:challenge/85943/assignment-2-dechat
	@git push https://github.com/nagahole/dechat

ngrok:
	@ngrok tcp 5001


test: build-javascript dotest

build-javascript:
	$(MAKE) -C .. build-javascript

dotest:
	@./node_modules/.bin/mocha \
		--require test/common \
		test/tests.js

.PHONY: test build-javascript dotest

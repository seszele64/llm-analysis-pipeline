.PHONY: install test package clean

install:
	pip install -r requirements.txt -t ./package

test:
	pytest

package: install
	cd package && zip -r ../function.zip .
	zip -g function.zip handler.py

clean:
	rm -rf package function.zip
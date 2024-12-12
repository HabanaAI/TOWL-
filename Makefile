PACKAGES=towl-db towl-user towl-instrument
.PHONY: build docs all


all:
	@echo "Commands:"
	@echo "   make build - runs poetry command to build package and moves them into dist"
	@echo "   make docs - runs pdoc3 command to build API docs"
	@echo "   make install - installs towl-db and towl-user"
	@echo "   make install_edit - installs towl-db and towl-user in edit mode"

build:
	rm -rvf dist
	mkdir dist
	for pkg in ${PACKAGES}; do (cd $${pkg}; poetry build -o ../dist); done
	
docs:
	rm -rvf docs
	for pkg in ${PACKAGES}; do (cd $${pkg}; pdoc3 --html -f -o ../docs towl); done
	rm -rvf docs/towl/towl-db docs/towl/towl-user docs/towl/towl-instrument docs/towl/index.html

install:
	for pkg in ${PACKAGES}; do (cd $${pkg}; python3 -m pip install .); done

install_edit:
	for pkg in ${PACKAGES}; do (cd $${pkg}; python3 -m pip install -e .); done

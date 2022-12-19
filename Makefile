# all: unittests

# clean:
# 	$(info -> Makefile: cleanup previous builds ... )
# 	@(rm -rf src/test/__pycache__ src/carcano/foolist/__pycache__ src/bin/__pycache__)
# 	@(rm -rf src/carcano_foolist.egg-info src/.eggs)
# 	@(rm -rf src/dist src/build)

# unittests:
# 	$(info -> Makefile: Launching unit tests ...)
# 	@(cd src; python3 setup.py nosetests >/dev/null)
flask:
	cd app && export FLASK_APP=app && export FLASK_ENV=development && flask run
image:
	docker build -t flask-app .
container:
	docker run -it --net=host flask-app
pep8:
	cd app && autopep8 --aggressive --aggressive --in-place --recursive .
test:
	cd tests && pytest
test-verbose:
	cd tests && pytest -s
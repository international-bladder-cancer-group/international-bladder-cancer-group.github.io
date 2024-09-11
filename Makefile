all: style render

render: render.py
	venv/bin/python render.py

style: style.sass
	sass style.sass sources/style.css

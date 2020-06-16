lint:
	@make black
	@make flake8
clean:
	git clean -Xdf
black:
	black -t py27 -l 79 .
flake8:
	flake8 -j8 .

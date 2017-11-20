from flask import render_template

from . import main

@main.errorhandler(404) #catch 404 error
def page_not_found(e):
	return render_template('404.html'), 404

@main.errorhandler(500) #catch 500 error
def internal_server_error(e):
	return render_template('500.html'), 500
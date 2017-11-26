from flask import g, jsonify
from flask_httpauth import HTTPBasicAuth

from . import api
from ..models import User
from .errors import unauthorized, forbidden

auth = HTTPBasicAuth()

@api.before_request
@auth.login_required
def before_request():
	if not g.current_user.confirmed:
		return forbidden('Uncomfirmed account')

#do this when every request from client
#return True means current user can access the resource
#return False the auth.error_handler will catch this error
@auth.verify_password 
def verify_password(email_or_token, password):
	if email_or_token == '':
		return False
	if password == '':
		g.current_user = User.verify_auth_token(email_or_token)
		g.token_used = True
		return g.current_user is not None
	user = User.query.filter_by(email=email_or_token).first()
	if not user:
		return False
	g.current_user = user
	g.token_used = False
	return user.verify_password(password)

@auth.error_handler
def auth_error():
	return unauthorized('Invalid credentials')

@api.route('/token')
def get_token():
	if g.token_used:
		return forbidden('You cant use old token to apply new token')
	return jsonify({'token': g.current_user.generate_auth_token(expiration=3600), \
		'expiration': 3600})
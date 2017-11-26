from flask import jsonify, request, g, current_app, url_for
from . import api
from .errors import forbidden
from .. import db
from ..models import User, Question, Answer, Activity, Follow


@api.route('/user/<int:id>')
def get_user(id):
	user = User.query.get_or_404(id)
	return jsonify(user.to_json())

@api.route('/user/<int:id>/questions/')
def get_user_questions(id):
	user = User.query.get_or_404(id)
	page = request.args.get('page', 1, type=int)
	pagination = user.questions.order_by(Question.timestamp.desc()).paginate( \
		page, per_page=current_app.config['FLASKY_POSTS_PER_PAGE'], \
		error_out=False)
	questions = pagination.items
	prev = None
	if pagination.has_prev:
		prev = url_for('api.get_user_questions', id=id, page=page-1, \
					   _external=True)
	next =None
	if pagination.has_next:
		next = url_for('api.get_user_questions', id=id, page=page+1, \
					   _external=True)
	return jsonify({
		'question': [question.to_json() for question in questions],
		'prev': prev,
		'next': next,
		'count': pagination.total
		})


@api.route('/user/<int:id>/answers/')
def get_user_answers(id):
	user = User.query.get_or_404(id)
	page = request.args.get('page', 1, type=int)
	pagination = user.answers.order_by(Answer.timestamp.desc()).paginate( \
		page, per_page=current_app.config['FLASKY_POSTS_PER_PAGE'], \
		error_out=False)
	answers = pagination.items
	prev = None
	if pagination.has_prev:
		prev = url_for('api.get_user_answers', id=id, page=page-1, \
					   _external=True)
	next =None
	if pagination.has_next:
		next = url_for('api.get_user_answers', id=id, page=page+1, \
					   _external=True)
	return jsonify({
		'answers': [answer.to_json() for answer in answers],
		'prev': prev,
		'next': next,
		'count': pagination.total
		})


@api.route('/user/<int:id>/activities/')
def get_user_activities(id):
	user = User.query.get_or_404(id)
	page = request.args.get('page', 1, type=int)
	pagination = user.activities.order_by(Activity.timestamp.desc()).paginate( \
		page, per_page=current_app.config['FLASKY_POSTS_PER_PAGE'], \
		error_out=False)
	activities = pagination.items
	prev = None
	if pagination.has_prev:
		prev = url_for('api.get_user_activities', id=id, page=page-1, \
					   _external=True)
	next =None
	if pagination.has_next:
		next = url_for('api.get_user_activities', id=id, page=page+1, \
					   _external=True)
	return jsonify({
		'activities': [activity.to_json() for activity in activities],
		'prev': prev,
		'next': next,
		'count': pagination.total
		})

@api.route('/user/<int:id>/timeline/')
def get_user_followed_activities(id):
	user = User.query.get_or_404(id)
	if user != g.current_user:
		return forbidden('Insufficient permissions')
	page = request.args.get('page', 1, type=int)
	pagination = user.followed_activities().order_by(Activity.timestamp.desc()).paginate( \
		page, per_page=current_app.config['FLASKY_POSTS_PER_PAGE'], \
		error_out=False)
	activities = pagination.items
	prev = None
	if pagination.has_prev:
		prev = url_for('api.get_user_followed_activities', id=id, page=page-1, \
					   _external=True)
	next =None
	if pagination.has_next:
		next = url_for('api.get_user_followed_activities', id=id, page=page+1, \
					   _external=True)
	return jsonify({
		'activities': [activity.to_json() for activity in activities],
		'prev': prev,
		'next': next,
		'count': pagination.total
		})

@api.route('/user/<int:id>/followers/')
def get_user_followers(id):
	user = User.query.get_or_404(id)
	page = request.args.get('page', 1, type=int)
	pagination = user.followers.paginate( \
		page, per_page=current_app.config['FLASKY_POSTS_PER_PAGE'], \
		error_out=False)
	followers = pagination.items
	prev =None
	if pagination.has_prev:
		prev = url_for('api.get_user_followers', id=id, page=page-1, \
					   _external=True)
	next =None
	if pagination.has_next:
		next = url_for('api.get_user_followers', id=id, page=page+1, \
					   _external=True)
	return jsonify({
		'followers': [follower.follower.to_json() for follower in followers],
		'prev': prev,
		'next': next,
		'count': pagination.total
		})

@api.route('/user/<int:id>/followeds/')
def get_user_followeds(id):
	user = User.query.get_or_404(id)
	page = request.args.get('page', 1, type=int)
	pagination = user.followeds.paginate( \
		page, per_page=current_app.config['FLASKY_POSTS_PER_PAGE'], \
		error_out=False)
	followeds = pagination.items
	prev = None
	if pagination.has_prev:
		prev = url_for('api.get_user_followeds', id=id, page=page-1, \
					   _external=True)
	next =None
	if pagination.has_next:
		next = url_for('api.get_user_followeds', id=id, page=page+1, \
					   _external=True)
	return jsonify({
		'followeds': [followed.followed.to_json() for followed in followeds],
		'prev': prev,
		'next': next,
		'count': pagination.total
		})

@api.route('/user/<int:id>/follow')
def follow_user(id):
	user = User.query.get_or_404(id)
	if not g.current_user.is_following(user):
		g.current_user.follow(user)
	return jsonify(user.to_json())

@api.route('/user/<int:id>/unfollow')
def unfollow_user(id):
	user = User.query.get_or_404(id)
	if g.current_user.is_following(user):
		g.current_user.unfollow(user)
	return jsonify(user.to_json())

#add route for register latter

@api.route('/user/<int:id>', methods=['PUT'])
def edit_user(id):
	user = User.query.get_or_404(id)
	if user != g.current_user:
		return forbidden('Insufficient permissions')
	user.location = request.json.get('location', user.location)
	user.about_me = request.json.get('about_me', user.about_me)
	db.session.add(user)
	return jsonify(user.to_json())










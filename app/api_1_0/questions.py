from datetime import datetime
from flask import jsonify, request, g, abort, url_for, current_app
from .. import db
from ..models import Question, Activity
from . import api
from .errors import forbidden

@api.route('/questions/')
def get_questions():
	page = request.args.get('page', 1, type=int)
	pagination = Question.query.paginate(
		page, per_page=current_app.config['FLASKY_POSTS_PER_PAGE'],
		error_out=False)
	questions = pagination.items
	prev = None
	if pagination.has_prev:
		prev = url_for('api.get_questions', page=page-1, _external=True)
	next = None
	if pagination.has_next:
		next = url_for('api.get_questions', page=page+1, _external=True)
	return jsonify({
		'questions': [question.to_json() for question in questions],
		'prev': prev,
		'next': next,
		'count': pagination.total
	})

@api.route('/question/<int:id>')
def get_question(id):
	question = Question.query.get_or_404(id)
	return jsonify(question.to_json())

@api.route('/question/', methods=['POST'])
def new_question():
	question = Question.from_json(request.json)
	question.author = g.current_user
	add_activity = Activity(owner=g.current_user, question=question, \
			action=1, timestamp=datetime.utcnow())
	db.session.add(add_activity)
	db.session.add(question)
	db.session.commit()
	return jsonify(question.to_json()), 201, \
	{'Location': url_for('api.get_question', id=question.id, _external=True)}

@api.route('/question/<int:id>', methods=['PUT'])
def edit_question(id):
	question = Question.query.get_or_404(id)
	if question.author != g.current_user:
		return forbidden('Insufficient permissions')
	question.title = request.json.get('title', question.title)
	db.session.add(question)
	return jsonify(question.to_json())

@api.route('/question/<int:id>/focus_or_cancel')
def focus_or_cancel(id):
	question = Question.query.get_or_404(id)
	activity = g.current_user.focusStatus(id)
	if not activity:
		add_activity = Activity(owner=g.current_user, question=question, \
			action=3, timestamp=datetime.utcnow())
		question.focuses += 1
		db.session.add(add_activity)
		db.session.add(question)
		return jsonify({
			'question': question.to_json(),
			'action': 'focus'
			})
	else:
		question.focuses -= 1
		db.session.delete(activity)
		db.session.add(question)
		return jsonify({
			'question': question.to_json(),
			'action': 'cancel'
			})
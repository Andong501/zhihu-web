from datetime import datetime
from flask import jsonify, request, g, current_app, url_for

from . import api
from .. import db
from ..models import Question, Answer, Activity
from .errors import forbidden

@api.route('/question/<int:q_id>/answer/<int:a_id>')
def get_answer(q_id, a_id):
	question = Question.query.get_or_404(q_id)
	answer = question.answers.filter_by(id=a_id).first_or_404()
	return jsonify(answer.to_json())

@api.route('/question/<int:id>/answers/')
def get_question_answers(id):
	question = Question.query.get_or_404(id)
	page = request.args.get('page', 1, type=int)
	pagination = question.answers.order_by(Answer.timestamp.desc()).paginate( \
		page, per_page=current_app.config['FLASKY_POSTS_PER_PAGE'], \
		error_out=False)
	answers = pagination.items
	prev = None
	if pagination.has_prev:
		prev = url_for('api.get_question_answers', id=id, page=page-1,
					   _external=True)
	next = None
	if pagination.has_next:
		next = url_for('api.get_question_answers', id=id, page=page+1,
					   _external=True)
	return jsonify({
		'answer': [answer.to_json() for answer in answers],
		'prev': prev,
		'next': next,
		'count': pagination.total
		})

@api.route('/question/<int:id>/answers/', methods=['POST'])
def new_question_answer(id):
	question = Question.query.get_or_404(id)
	answer = Answer.from_json(request.json)
	answer.question = question
	answer.author = g.current_user
	add_activity = Activity(owner=g.current_user, answer=answer, \
			action=2, timestamp=datetime.utcnow())
	db.session.add(add_activity)
	db.session.add(answer)
	db.session.commit()
	return jsonify(answer.to_json()), 201, \
	{'Location': url_for('api.get_answer', \
		q_id=question.id, a_id=answer.id, _external=True)}

@api.route('/question/<int:q_id>/answer/<int:a_id>', methods=['PUT'])
def edit_question_answer(q_id, a_id):
	question = Question.query.get_or_404(q_id)
	answer = question.answers.filter_by(id=a_id).first_or_404()
	if answer.author != g.current_user:
		return forbidden('Insufficient permissions')
	answer.body = request.json.get('body', answer.body)
	db.session.add(answer)
	return jsonify(answer.to_json())

@api.route('/answer/<int:id>/vote_or_cancel')
def vote_or_cancel(id):
	answer = Answer.query.get_or_404(id)
	activity = g.current_user.voteStatus(id)
	if not activity:
		add_activity = Activity(owner=g.current_user, answer=answer, \
			action=4, timestamp=datetime.utcnow())
		answer.likes += 1
		answer.author.likes += 1
		db.session.add(add_activity)
		db.session.add(answer)
		return jsonify({
			'answer': answer.to_json(),
			'action': 'vote'
			})
	else:
		answer.likes -= 1
		answer.author.likes -= 1
		db.session.delete(activity)
		db.session.add(answer)
		return jsonify({
			'answer': answer.to_json(),
			'action': 'cancel'
			})

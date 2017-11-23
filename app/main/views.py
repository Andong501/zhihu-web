from datetime import datetime
from flask import render_template, session, redirect, url_for,flash, abort, request, current_app, jsonify
from flask_login import login_required, current_user

from . import main
from .forms import EditUserForm, AskForm, AnswerForm
from .. import db
from ..models import User, Question, Follow, Answer, Activity

@main.route('/', methods=['GET', 'POST'])
@login_required
def index():
	title = request.form.get('title')
	click = request.form.get('click')
	if title and click:
		question = Question(title=title, author=current_user._get_current_object())
		activity = Activity(owner=current_user._get_current_object(), question=question, action=1)
		db.session.add(question)
		db.session.add(activity)
		return 'ok'
	elif click:
		return 'error'
	else:
		query = current_user.followed_activities()
		page = request.args.get('page', 1, type=int)
		pagination = query.order_by(Activity.timestamp.desc()).paginate(\
			page, per_page=current_app.config['FLASKY_POSTS_PER_PAGE'], error_out=False)
		activities = pagination.items
		return render_template('index.html', activities=activities, pagination=pagination)

@main.route('/user/<username>')
@login_required
def user(username):
	user = User.query.filter_by(username=username).first_or_404()
	page = request.args.get('page', 1, type=int)
	pagination = user.activities.order_by(Activity.timestamp.desc()).paginate(\
		page, per_page=current_app.config['FLASKY_POSTS_PER_PAGE'], error_out=False)
	activities = pagination.items
	return render_template('user.html', user=user, activities=activities, pagination=pagination)

@main.route('/user/edit', methods=['GET', 'POST'])
@login_required
def editUser():
		form = EditUserForm()
		if form.validate_on_submit():
			current_user.location = form.location.data
			current_user.about_me = form.about_me.data
			db.session.add(current_user)
			flash('Your profile has been updated successfully !')
			return redirect(url_for('main.user', username=current_user.username))
		form.location.data = current_user.location
		form.about_me.data = current_user.about_me
		return render_template('edit_user.html', form=form)

@main.route('/question/<int:id>', methods=['GET', 'POST'])
@login_required
def question(id):
	question = Question.query.get_or_404(id)
	body = request.form.get('body')
	click = request.form.get('click')
	if body and click:
		add_answer = Answer(body=body, question=question, \
			author=current_user._get_current_object())
		activity = Activity(owner=current_user._get_current_object(), answer=add_answer, action=2)
		db.session.add(add_answer)
		db.session.add(activity)
		add_answer = db.session.merge(add_answer)
		return jsonify({
			'status': 'ok',
			'location': url_for('main.answer', q_id=question.id, a_id=add_answer.id)
			})
	elif click:
		return 'error'
	else:
		page = request.args.get('page', 1, type=int)
		pagination = question.answers.order_by(Answer.timestamp.desc()).paginate(\
			page, per_page=current_app.config['FLASKY_POSTS_PER_PAGE'], error_out=False)
		answers = pagination.items
		return render_template('question.html', questions=[question], \
			answers=answers, pagination=pagination) #Need to add []

@main.route('/question/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def editQuestion(id):
	question = Question.query.get_or_404(id)
	if current_user != question.author:
		abort(403)
	form = AskForm()
	if form.validate_on_submit():
		question.title = form.title.data
		db.session.add(question)
		flash('The question has been updated.')
		return redirect(url_for('main.question', id=question.id))
	form.title.data = question.title
	return render_template('edit_question.html', form=form)

@main.route('/question/<int:q_id>/answer/<int:a_id>', methods=['GET', 'POST'])
@login_required
def answer(q_id, a_id):
	question = Question.query.get_or_404(q_id)
	answer = question.answers.filter_by(id=a_id).first_or_404()
	form = AnswerForm()
	if form.validate_on_submit():
		add_answer = Answer(body=form.body.data, question=question, \
			author=current_user._get_current_object())
		activity = Activity(owner=current_user._get_current_object(), answer=add_answer, action=2)
		db.session.add(add_answer)
		db.session.add(activity)
		add_answer = db.session.merge(add_answer)
		return redirect(url_for('main.answer', q_id=question.id, a_id=add_answer.id))
	page = request.args.get('page', 1, type=int)
	query = question.answers.filter(Answer.id!=a_id)
	pagination = query.order_by(Answer.timestamp.desc()).paginate(\
		page, per_page=current_app.config['FLASKY_POSTS_PER_PAGE'], error_out=False)
	answers = pagination.items
	return render_template('answer.html', form=form, questions=[question], \
		answer=answer, answers=answers, pagination=pagination) #Need to add []

@main.route('/question/<int:q_id>/answer/<int:a_id>/edit', methods=['GET', 'POST'])
@login_required
def editAnswer(q_id, a_id):
	question = Question.query.get_or_404(q_id)
	answer = question.answers.filter_by(id=a_id).first_or_404()
	if current_user != answer.author:
		abort(403)
	form = AnswerForm()
	if form.validate_on_submit():
		answer.body = form.body.data
		db.session.add(answer)
		flash('The answer has been update.')
		return redirect(url_for('main.answer', q_id=question.id, a_id=answer.id))
	form.body.data = answer.body
	return render_template('edit_answer.html', form=form)

@main.route('/vote_or_cancel', methods=['POST'])
def vote_or_cancel():
	if not current_user.is_authenticated:
		return jsonify({
			'status': 302,
			'location': url_for('auth.login', next=request.refferer.replace(\
			url_for('main.index', _external=True)[:-1], ''))
			})
	a_id = int(request.form.get('id'))
	answer = Answer.query.get_or_404(a_id)
	activity = current_user.voteStatus(a_id)
	if not activity:
		#add activity
		add_activity = Activity(owner=current_user._get_current_object(), answer=answer, \
			action=4, timestamp=datetime.utcnow())
		#answers' like add one
		answer.likes += 1
		#authors' like add one
		answer.author.likes += 1
		db.session.add(add_activity)
		db.session.add(answer)
		return 'vote'
	else:
		#answers' like sub one
		answer.likes -= 1
		#authors' like sub one
		answer.author.likes -= 1
		#remove activity
		db.session.delete(activity)
		db.session.add(answer)
		return 'cancel'

@main.route('/focus_or_cancel', methods=['POST'])
def focus_or_cancel():
	if not current_user.is_authenticated:
		return jsonify({
			'status': 302,
			'location': url_for('auth.login', next=request.refferer.replace(\
			url_for('main.index', _external=True)[:-1], ''))
			})
	q_id = int(request.form.get('id'))
	question = Question.query.get_or_404(q_id)
	activity = current_user.focusStatus(q_id)
	if not activity:
		add_activity = Activity(owner=current_user._get_current_object(), question=question, \
			action=3, timestamp=datetime.utcnow())
		question.focuses += 1
		db.session.add(add_activity)
		db.session.add(question)
		return 'focus'
	else:
		question.focuses -= 1
		db.session.delete(activity)
		db.session.add(question)
		return 'cancel'

@main.route('/follow/<username>')
@login_required
def follow(username):
	user = User.query.filter_by(username=username).first()
	if user is None:
		flash('Invalid User!')
		return redirect(url_for('main.index'))
	if current_user.is_following(user):
		flash('You are already following this user!')
		return redirect(url_for('main.user', username=username))
	current_user.follow(user)
	flash('You are now following %s.' % username)
	return redirect(url_for('main.user', username=username))

@main.route('/unfollow/<username>')
@login_required
def unfollow(username):
	user = User.query.filter_by(username=username).first()
	if user is None:
		flash('Invalid user!')
		return redirect(url_for('main.index'))
	if not current_user.is_following(user):
		flash('You are not following thie user!')
		return redirect(url_for('main.user', username=username))
	current_user.unfollow(user)
	flash('You are not following %s anymore.' % username)
	return redirect(url_for('main.user', username=username))

@main.route('/user/<username>/followers')
@login_required
def followers(username):
	user = User.query.filter_by(username=username).first()
	if user is None:
		flash('Invalid user!')
		return redirect(url_for('main.index'))
	page = request.args.get('page', 1, type=int)
	pagination = user.followers.paginate(page, \
		per_page=current_app.config['FLASKY_FOLLOWERS_PER_PAGE'], error_out=False)
	follows = [{'user': item.follower, 'timestamp': item.timestamp} \
		for item in pagination.items]
	return render_template('followers.html', user=user, title="Followers of", \
		endpoint='main.followers', pagination=pagination, follows=follows)

@main.route('/user/<username>/followed_by')
@login_required
def followed_by(username):
	user = User.query.filter_by(username=username).first()
	if user is None:
		flash('Invalid user!')
		return redirect(url_for('main.index'))
	page = request.args.get('page', 1, type=int)
	pagination = user.followeds.paginate(page, \
		per_page=current_app.config['FLASKY_FOLLOWERS_PER_PAGE'], error_out=False)
	follows = [{'user': item.followed, 'timestamp': item.timestamp} \
		for item in pagination.items]
	return render_template('followers.html', user=user, title="Followed by", \
		endpoint='main.followed_by', pagination=pagination, follows=follows)






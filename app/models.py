from datetime import datetime
import hashlib
from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from flask import current_app, request, url_for
from flask_login import UserMixin, current_user

from app.exceptions import ValidationError
from . import db, login_manager

class Follow(db.Model):
	__tablename__ = 'follows'
	follower_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
	followed_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
	timestamp = db.Column(db.DateTime, default=datetime.utcnow)


class User(UserMixin, db.Model):
	__tablename__ = 'users'
	id = db.Column(db.Integer, primary_key=True)
	email = db.Column(db.String(64), unique=True, index=True)
	username = db.Column(db.String(64), unique=True, index=True)
	password_hash = db.Column(db.String(128))
	confirmed = db.Column(db.Boolean, default=False)
	location = db.Column(db.String(64))
	about_me = db.Column(db.Text())
	member_since = db.Column(db.DateTime(), default=datetime.utcnow)
	last_seen = db.Column(db.DateTime(), default=datetime.utcnow)
	avatar_hash = db.Column(db.String(32))
	likes = db.Column(db.Integer, default=0)

	questions = db.relationship('Question', backref='author', lazy='dynamic')
	answers = db.relationship('Answer', backref='author', lazy='dynamic')
	activities = db.relationship('Activity', backref='owner', lazy='dynamic')
	#user's fans
	followers = db.relationship('Follow', \
		foreign_keys=[Follow.followed_id], backref=db.backref('followed', \
		lazy='joined'), lazy='dynamic', cascade='all, delete-orphan')
	#user's idols
	followeds = db.relationship('Follow', \
		foreign_keys=[Follow.follower_id], \
		backref=db.backref('follower', lazy='joined'), \
		lazy='dynamic', cascade='all, delete-orphan')


	@staticmethod
	#make fake data of User
	def generate_fake(count=100): 
		from sqlalchemy.exc import IntegrityError
		from random import seed
		import forgery_py
		seed()
		for i in range(count):
			u = User(email=forgery_py.internet.email_address(),
					username=forgery_py.internet.user_name(True),
					password=forgery_py.lorem_ipsum.word(),
					confirmed=True,
					location=forgery_py.address.city(),
					about_me=forgery_py.lorem_ipsum.sentence(),
					member_since=forgery_py.date.date(True))
			db.session.add(u)
			try:
				db.session.commit()
			except IntegrityError:
				db.session.rollback()

	@staticmethod
	def add_self_follows():
		for user in User.query.all():
			if not user.is_following(user):
				user.follow(user)
				db.session.add(user)
				db.session.commit()

	def __init__(self, **kwargs):
		super(User, self).__init__(**kwargs)
		#restore the avatar_hash of email
		if self.email is not None and self.avatar_hash is None: 
			self.avatar_hash = hashlib.md5(self.email.encode('utf-8')).hexdigest()
		#follow self
		#why cannot use self.follow(self)?
		self.followeds.append(Follow(followed=self))


	@property
	def password(self):
		raise AttributeError('password is not a readable attribute')
	@password.setter
	def password(self, password):
		self.password_hash = generate_password_hash(password)


	def verify_password(self, password):
		return check_password_hash(self.password_hash, password)

	def generate_confirmation_token(self, expiration=3600):
		s = Serializer(current_app.config['SECRET_KEY'], expiration)
		return s.dumps({'confirm': self.id})

	def confirm(self, token):
		s = Serializer(current_app.config['SECRET_KEY'])
		try:
			data = s.loads(token)
		except:
			return False
		if data.get('confirm') != self.id:
			return False
		self.confirmed = True
		db.session.add(self)
		return True

	def generate_auth_token(self, expiration):
		s = Serializer(current_app.config['SECRET_KEY'], expiration)
		return s.dumps({'id': self.id})

	@staticmethod
	def verify_auth_token(token):
		s = Serializer(current_app.config['SECRET_KEY'])
		try:
			data = s.loads(token)
		except:
			return None
		return User.query.get(data['id'])

	def to_json(self):
		json_user = {
			'url': url_for('api.get_user', id=self.id, _external=True),
			'username': self.username,
			'member_since': self.member_since,
			'last_seen': self.last_seen,
			'location': self.location,
			'about_me' : self.about_me,
			'questions': url_for('api.get_user_questions', id=self.id, _external=True),
			'answers': url_for('api.get_user_answers', id=self.id, _external=True),
			'activities': url_for('api.get_user_activities', id=self.id, _external=True),
			'followed_activities': url_for('api.get_user_followed_activities', \
				id=self.id, _external=True),
			'followers': url_for('api.get_user_followers', id=self.id, _external=True),
			'followeds': url_for('api.get_user_followeds', id=self.id, _external=True),
			'question_count': self.questions.count(),
			'answer_count': self.answers.count(),
			'followed_count': self.followeds.count(),
			'follower_count': self.followers.count(),
			'like_count': self.likes
		}
		return json_user

	#update last_seen before every request
	def ping(self): 
		self.last_seen = datetime.utcnow()
		db.session.add(self)

	#get gravatar head portrait
	def gravatar(self, size=100, default='identicon', rating='g'): 
		if request.is_secure:
			url = 'https://secure.gravatar.com/avatar'
		else:
			url = 'http://www.gravatar.com/avatar'
		hash = self.avatar_hash or hashlib.md5(self.email.encode('utf-8')).hexdigest()
		return '{url}/{hash}?s={size}&d={default}&r={rating}'.format(url=url, \
			hash=hash, size=size, default=default, rating=rating)

	def follow(self, user):
		if not self.is_following(user):
			f = Follow(follower=self, followed=user)
			db.session.add(f)

	def unfollow(self, user):
		f = self.followeds.filter_by(followed_id=user.id).first()
		if f:
			db.session.delete(f)

	def is_following(self, user):
		return self.followeds.filter_by(followed_id=user.id).first() is not None

	def is_followed_by(self, user):
		return self.followers.filter_by(follower_id=user.id).first() is not None

	def followed_questions(self):
		#join search would be faster than embedded search
		#return a query
		return Question.query.join(Follow, Question.author_id==Follow.followed_id)\
		.filter(Follow.follower_id==self.id)

	def followed_activities(self):
		#join search would be faster than embedded search
		#return a query
		return Activity.query.join(Follow, Activity.owner_id==Follow.followed_id)\
		.filter(Follow.follower_id==self.id)

	def voteStatus(self, id):
		answer = Answer.query.get_or_404(id)
		activity = Activity.query.filter(Activity.owner==self, \
			Activity.answer==answer, Activity.action==4).first()
		return activity

	def focusStatus(self, id):
		question = Question.query.get_or_404(id)
		activity = Activity.query.filter(Activity.owner==self, \
			Activity.question==question, Activity.action==3).first()
		return activity

	def __repr__(self):
		return '<User %r>' % self.username


@login_manager.user_loader
def load_user(user_id):
	return User.query.get(int(user_id))


class Question(db.Model):
	__tablename__ = 'questions'
	id = db.Column(db.Integer, primary_key=True)
	title = db.Column(db.Text())
	timestamp = db.Column(db.DateTime(), index=True, default=datetime.utcnow)
	author_id = db.Column(db.Integer, db.ForeignKey('users.id'))
	focuses = db.Column(db.Integer, default=0)

	answers = db.relationship('Answer', backref='question', lazy='dynamic')
	activities = db.relationship('Activity', backref='question', lazy='dynamic')


	@staticmethod
	#make fake data of Question
	def generate_fake(count=100): 
		from random import seed, randint
		import forgery_py
		seed()
		user_count = User.query.count()
		for i in range(count):
			timestamp = forgery_py.date.date(True)
			u = User.query.offset(randint(0, user_count - 1)).first()
			p = Question(title=forgery_py.lorem_ipsum.sentences(randint(1, 5)), \
				timestamp=timestamp, author=u)
			ac = Activity(action=1, timestamp=timestamp, \
				question=p, answer=None, owner=u)
			db.session.add(p)
			db.session.add(ac)
			db.session.commit()

	def to_json(self):
		json_question = {
			'url': url_for('api.get_question', id=self.id, _external=True),
			'title': self.title,
			'timestamp': self.timestamp,
			'author': url_for('api.get_user', id=self.author_id, _external=True),
			'answers': url_for('api.get_question_answers', id=self.id, _external=True),
			'answer_count': self.answers.count(),
			'focus_count': self.focuses
		}
		return json_question

	@staticmethod
	def from_json(json_question):
		title = json_question.get('title')
		if title is None or title == '':
			raise ValidationError('question does not have a title')
		return Question(title=title)


class Answer(db.Model):
	__tablename__ = 'answers'
	id = db.Column(db.Integer, primary_key=True)
	body = db.Column(db.Text())
	timestamp = db.Column(db.DateTime(), default=datetime.utcnow)
	question_id = db.Column(db.Integer, db.ForeignKey('questions.id'))
	author_id = db.Column(db.Integer, db.ForeignKey('users.id'))
	likes = db.Column(db.Integer,default=0)

	activities = db.relationship('Activity', backref='answer', lazy='dynamic')

	@staticmethod
	#make fake data of Answer
	def generate_fake(count=200):
		from random import seed, randint
		import forgery_py
		seed()
		user_count = User.query.count()
		question_count = Question.query.count()
		for i in range(count):
			timestamp = forgery_py.date.date(True)
			u = User.query.offset(randint(0, user_count -1)).first()
			p = Question.query.offset(randint(0, question_count)).first()
			a = Answer(body=forgery_py.lorem_ipsum.sentences(randint(1, 5)), \
				timestamp=timestamp, author=u, question=p)
			ac = Activity(action=2, timestamp=timestamp, \
				question=None, answer=a, owner=u)
			db.session.add(a)
			db.session.add(ac)
			db.session.commit()

	def to_json(self):
		json_answer = {
			'url': url_for('api.get_answer', q_id=self.question_id, a_id=self.id, _external=True),
			'body': self.body,
			'timestamp': self.timestamp,
			'author': url_for('api.get_user', id=self.author_id, _external=True),
			'question': url_for('api.get_question', id=self.question_id, _external=True),
			'like_count': self.likes
		}
		return json_answer

	@staticmethod
	def from_json(json_answer):
		body = json_answer.get('body')
		if body is None or body == '':
			raise ValidationError('answer does not have a body')
		return Answer(body=body)


class Activity(db.Model):
	__tablename__ = 'activities'
	id = db.Column(db.Integer, primary_key=True)
	owner_id = db.Column(db.Integer, db.ForeignKey('users.id'))
	question_id = db.Column(db.Integer, db.ForeignKey('questions.id'))
	answer_id = db.Column(db.Integer, db.ForeignKey('answers.id'))
	action = db.Column(db.Integer) #1=ask, 2=answer, 3=focus, 4=like
	timestamp = db.Column(db.DateTime(), index=True, default=datetime.utcnow)

	@staticmethod
	def generate_fake(count=100):
		from random import seed, randint
		import forgery_py
		seed()
		user_count = User.query.count()
		question_count = Question.query.count()
		answer_count = Answer.query.count()
		for i in range(count):
			q = Question.query.offset(randint(0, question_count - 1)).first()
			a = None
			u = q.author
			ac = Activity(action=1, timestamp=forgery_py.date.date(True), \
				question=q, answer=a, owner=u)
			db.session.add(ac)
			db.session.commit()
		
		for i in range(count):
			q = None
			a = Answer.query.offset(randint(0, answer_count - 1)).first()
			u = a.author
			ac = Activity(action=2, timestamp=forgery_py.date.date(True), \
				question=q, answer=a, owner=u)
			db.session.add(ac)
			db.session.commit()

	def to_json(self):
		if self.question_id:
			json_activity = {
				'url': url_for('api.get_activity', id=self.id, _external=True),
				'action': self.action,
				'timestamp': self.timestamp,
				'owner': url_for('api.get_user', id=self.owner_id, _external=True),
				'question': url_for('api.get_question', id=self.question_id, _external=True),
			}
		else:
			json_activity = {
				'url': url_for('api.get_activity', id=self.id, _external=True),
				'action': self.action,
				'timestamp': self.timestamp,
				'owner': url_for('api.get_user', id=self.owner_id, _external=True),
				'answer': url_for('api.get_answer', q_id=self.answer.question_id, a_id=self.answer_id, _external=True),
			}
		return json_activity
















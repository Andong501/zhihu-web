from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, TextAreaField
from wtforms.validators import Required, Length


class EditUserForm(FlaskForm):
	location = StringField("Location", validators=[Length(0, 64)])
	about_me = TextAreaField("About Me")
	submit = SubmitField("Submit")

class AskForm(FlaskForm):
	title = TextAreaField("What do you want to ask ?", validators=[Required()])
	submit = SubmitField("Submit")

class AnswerForm(FlaskForm):
	body = TextAreaField("What is your mind about this question ?", validators=[Required()])
	submit = SubmitField("Submit")

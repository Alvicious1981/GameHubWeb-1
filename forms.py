from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, TextAreaField, SelectField, IntegerField
from wtforms.validators import DataRequired, Email, Length, EqualTo, NumberRange

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])

class RegisterForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=4, max=64)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])

class ReviewForm(FlaskForm):
    content = TextAreaField('Review', validators=[DataRequired(), Length(min=10)])
    rating = IntegerField('Rating', validators=[DataRequired(), NumberRange(min=1, max=5)])

class GuideForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired(), Length(max=200)])
    content = TextAreaField('Guide Content', validators=[DataRequired()])
    game_id = SelectField('Game', coerce=int, validators=[DataRequired()])

class GameFilterForm(FlaskForm):
    genre = SelectField('Genre', choices=[('all', 'All Genres')], default='all')

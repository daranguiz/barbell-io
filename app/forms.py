from flask_wtf import Form
from wtforms import StringField, BooleanField, TextAreaField, RadioField, DecimalField, IntegerField, SelectField
from wtforms.validators import DataRequired, Length, Optional

from .strong import *

class LoginForm(Form):
    openid = StringField('openid', validators=[DataRequired()])
    remember_me = BooleanField('remember_me', default=False)

class EditForm(Form):
    nickname = StringField('nickname', validators=[DataRequired()])
    about_me = TextAreaField('about_me', validators=[Length(min=0, max=140)])

    def __init__(self, original_nickname, *args, **kwargs):
        Form.__init__(self, *args, **kwargs)
        self.original_nickname = original_nickname

    def validate(self):
        if not Form.validate(self):
            return False
        if self.nickname.data == self.original_nickname:
            return True
        user = User.query.filter_by(nickname=self.nickname.data).first()
        if user != None:
            self.nickname.errors.append('This nickname is already in use. Please choose another one.')
            return False
        return True

class WilksForm(Form):
    sex = RadioField('sex', choices=[('male','Male'), ('female','Female')], default='male', validators=[DataRequired()])
    units = RadioField('units', choices=[('lb','Pounds'), ('kg','Kilograms')], default='lb', validators=[DataRequired()])
    weight = DecimalField('weight', validators=[DataRequired()])
    squat = DecimalField('squat', validators=[Optional()])
    bench = DecimalField('bench', validators=[Optional()])
    deadlift = DecimalField('deadlift', validators=[Optional()])

class TrackSetForm(Form):
    bw = DecimalField('bw')
    lift = SelectField('lift', choices=[(choice, choice) for choice in lift_choices], validators=[DataRequired()])
    weight = DecimalField('weight', validators=[DataRequired()])
    reps = IntegerField('reps', validators=[DataRequired()])
    rpe = DecimalField('rpe', validators=[Optional()])

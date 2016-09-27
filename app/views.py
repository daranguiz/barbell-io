from flask import render_template, flash, redirect, session, url_for, request, g
from flask.ext.login import login_user, logout_user, current_user, login_required
from datetime import datetime

from app import app, db, lm, oid
from .forms import LoginForm, EditForm, WilksForm, TrackSetForm
from .models import User, LiftEntry
from .strong import *


@app.route('/', methods=['GET', 'POST'])
@app.route('/index/', methods=['GET', 'POST'])
@login_required
def index():
    form = WilksForm()
    if form.validate_on_submit():
        flash('You are very strong! Your Wilks score is %.2f.' % (compute_wilks_from_form(form)))
        return redirect(url_for('index'))
    return render_template('index.html',
                           title='Home',
                           form=form)

@app.route('/track', methods=['GET', 'POST'])
@login_required
def track():
    form = TrackSetForm()
    if form.validate_on_submit():
        newLiftEntry = LiftEntry(lift=form.lift.data,
                                 bw=form.bw.data,
                                 weight=form.weight.data,
                                 reps=form.reps.data,
                                 timestamp=datetime.utcnow(),
                                 user_id=g.user.id)
        db.session.add(newLiftEntry)
        db.session.commit()
        flash('Your lift has been saved!')
        return redirect(url_for('track'))
    return render_template('track.html', form=form, title='Track')

@app.before_request
def before_request():
    g.user = current_user
    if g.user.is_authenticated:
        g.user.last_seen = datetime.utcnow()
        db.session.add(g.user)
        db.session.commit()


@app.route('/login', methods=['GET', 'POST'])
@oid.loginhandler
def login():
    if g.user is not None and g.user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        session['remember_me'] = form.remember_me.data
        return oid.try_login(form.openid.data, ask_for=['nickname', 'email'])
    return render_template('login.html',
                           title='Sign In',
                           form=form,
                           providers=app.config['OPENID_PROVIDERS'])


@oid.after_login
def after_login(resp):
    if resp.email is None or resp.email == "":
        flash('Invalid login. Please try again.')
        return redirect(url_for('login'))
    user = User.query.filter_by(email=resp.email).first()
    if user is None:
        nickname = resp.nickname
        if nickname is None or nickname == "":
            nickname = resp.email.split('@')[0]
        nickname = User.make_unique_nickname(nickname)
        user = User(nickname = nickname, email = resp.email)
        db.session.add(user)
        db.session.commit()
    remember_me = False
    if 'remember_me' in session:
        remember_me = session['remember_me']
        session.pop('remember_me', None)
    login_user(user, remember = remember_me)
    return redirect(request.args.get('next') or url_for('index'))


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))


@lm.user_loader
def load_user(id):
    return User.query.get(int(id))


@app.route('/user/<nickname>')
@login_required
def user(nickname):
    user = User.query.filter_by(nickname=nickname).first()
    if user == None:
        flash('User %s not found.' % nickname)
        return redirect(url_for('index'))
    lifts = user.lifts

    # LiftEntry.query.delete()
    # db.session.commit()

    # highchart stuff

    charts = []
    for idx, lift_choice in enumerate(lift_choices):
        cur_lift = lifts.filter_by(lift=lift_choice)

        cur_chart = {}
        cur_chart['chartID'] = 'chart' + str(idx)
        cur_chart['chart'] = {"renderTo": 'chartID_' + str(idx), "type": 'line', "height": 350}
        cur_chart['series'] = [{"name": 'Label', "data": [lift.weight for lift in cur_lift]}]
        cur_chart['chartTitle'] = {"text": lift_choice}
        cur_chart['xAxis'] = {"categories": [str(i) for i in range(cur_lift.count())]}
        cur_chart['yAxis'] = {"title": {"text": 'Weight in lbs'}}

        charts.append(cur_chart)


    return render_template('user.html',
                           title='Your Profile',
                           user=user,
                           charts=charts)


@app.route('/edit', methods=['GET', 'POST'])
@login_required
def edit():
    form = EditForm(g.user.nickname)
    if form.validate_on_submit():
        g.user.nickname = form.nickname.data
        g.user.about_me = form.about_me.data
        db.session.add(g.user)
        db.session.commit()
        flash('Your changes have been saved.')
        return redirect(url_for('edit'))
    else:
        form.nickname.data = g.user.nickname
        form.about_me.data = g.user.about_me
    return render_template('edit.html', form=form)

@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html'), 500
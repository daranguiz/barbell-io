from flask import render_template, make_response, flash, redirect, session, url_for, request, g
from flask.ext.login import login_user, logout_user, current_user, login_required
from authomatic.adapters import WerkzeugAdapter
from authomatic import Authomatic
from datetime import datetime

from app import app, db, lm, oid
from config import OAUTH_PROVIDERS
from .forms import LoginForm, EditForm, WilksForm, TrackSetForm
from .models import User, LiftEntry
from .strong import *


# Instantiate Authomatic.
authomatic = Authomatic(OAUTH_PROVIDERS, 'your secret string', report_errors=False)


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
    print('Current user: ' + str(g.user))
    if g.user.is_authenticated:
        g.user.last_seen = datetime.utcnow()
        db.session.add(g.user)
        db.session.commit()


@app.route('/login')
def login():
    return render_template('login.html')


@app.route('/login/<provider_name>', methods=['GET', 'POST'])
def oauth(provider_name):
    response = make_response()
    result = authomatic.login(WerkzeugAdapter(request, response), provider_name)

    if result:
        if result.user:
            # authomatic
            result.user.update()

            # User.query.delete()
            # db.session.commit()

            # Check if this user has been seen before
            user = User.query.filter_by(uid=result.user.id).first()

            if user == None:
                username = result.user.email.split('@')[0]
                user = User(uid = result.user.id,
                            username = User.make_unique_username(username),
                            email = result.user.email)
                db.session.add(user)
                db.session.commit()

                login_user(user, remember=True)
                return redirect(url_for('signup'))

            login_user(user, remember=True)

            return redirect(url_for('index'))

        return render_template('login.html', result=result)

    return response


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('login'))


@lm.user_loader
def load_user(id):
    return User.query.get(int(id))


@app.route('/user/<username>')
@app.route('/user/<username>/home')
@login_required
def user_home(username):
    user = User.query.filter_by(username=username).first()
    if user == None:
        flash('User %s not found.' % username)
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


    return render_template('user_home.html',
                           title='Your Profile',
                           user=user,
                           charts=charts)

@app.route('/user/<username>/placeholder1')
@login_required
def user_placeholder1(username):
    user = User.query.filter_by(username=username).first()
    if user == None:
        flash('User %s not found.' % username)
        return redirect(url_for('index'))

    return render_template('user_placeholder1.html',
                           title='Placeholder 1',
                           user=user)

@app.route('/user/<username>/placeholder2')
@login_required
def user_placeholder2(username):
    user = User.query.filter_by(username=username).first()
    if user == None:
        flash('User %s not found.' % username)
        return redirect(url_for('index'))

    return render_template('user_placeholder2.html',
                           title='Placeholder 2',
                           user=user)


@app.route('/edit', methods=['GET', 'POST'])
@login_required
def edit():
    form = EditForm(g.user.username)
    if form.validate_on_submit():
        g.user.username = form.username.data
        g.user.about_me = form.about_me.data
        db.session.add(g.user)
        db.session.commit()
        flash('Your changes have been saved.')
        return redirect(url_for('edit'))
    else:
        form.username.data = g.user.username
        form.about_me.data = g.user.about_me
    return render_template('edit.html', form=form)


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    form = EditForm(g.user.username)
    if form.validate_on_submit():
        g.user.username = form.username.data
        g.user.about_me = form.about_me.data
        db.session.add(g.user)
        db.session.commit()
        flash('Thanks for registering!')
        return redirect(url_for('index'))
    else:
        form.username.data = g.user.username
        form.about_me.data = g.user.about_me
    return render_template('signup.html', form=form)


@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html'), 500
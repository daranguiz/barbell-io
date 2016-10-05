from flask import render_template, make_response, flash, redirect, session, url_for, request, g
from flask.ext.login import login_user, logout_user, current_user, login_required
from authomatic.adapters import WerkzeugAdapter
from authomatic import Authomatic
from datetime import datetime
from sqlalchemy import asc, desc, func
import numpy as np

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

    # Prefill with last entry
    if request.method == 'GET':
        lastLift = LiftEntry.query.filter_by(user_id=g.user.id).order_by(desc(LiftEntry.id)).first()

        if lastLift is not None:
            form.lift.data = lastLift.lift
            form.bw.data = lastLift.bw
            form.weight.data = lastLift.weight
            form.reps.data = lastLift.reps

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
    units = user.units

    # LiftEntry.query.delete()
    # db.session.commit()

    # highchart stuff

    charts = []
    for idx, lift_choice in enumerate(lift_choices):
        cur_lift = lifts.filter_by(lift=lift_choice)

        if cur_lift.count() > 0:
            cur_chart = {}
            cur_chart['chartID'] = 'chart' + str(idx)
            cur_chart['chart'] = {"renderTo": 'chartID_' + str(idx), "type": 'spline'}
            cur_chart['series'] = [{"name": 'Weight', "data": [lift.weight for lift in cur_lift]}]
            cur_chart['chartTitle'] = {"text": lift_choice}
            cur_chart['xAxis'] = {"categories": [str(i) for i in range(cur_lift.count())]}
            cur_chart['yAxis'] = {"title": {"text": 'Weight in ' + units}}
            cur_chart['plotOptions'] = {}

            charts.append(cur_chart)


    return render_template('user_home.html',
                           title='Your Profile',
                           user=user,
                           charts=charts)

@app.route('/user/<username>/analytics')
@login_required
def user_analytics(username):
    user = User.query.filter_by(username=username).first()
    if user == None:
        flash('User %s not found.' % username)
        return redirect(url_for('index'))

    lifts = user.lifts
    units = user.units

    # 1RM
    charts = []
    for idx, lift_choice in enumerate(lift_choices):
        cur_lift = lifts.filter_by(lift=lift_choice)

        if cur_lift.count() > 0:
            cur_chart = {}
            cur_chart['chartID'] = 'chart_1rm' + str(idx)
            cur_chart['chart'] = {"renderTo": 'chartID_' + str(idx), "type": 'spline'}
            cur_chart['series'] = [{"name": 'Weight', "data": [estimate_1rm_epley(lift.weight, lift.reps) for lift in cur_lift]}]
            cur_chart['chartTitle'] = {"text": "Estimated 1RM: " + lift_choice}
            cur_chart['xAxis'] = {"categories": [str(i) for i in range(cur_lift.count())]}
            cur_chart['yAxis'] = {"title": {"text": 'Weight in ' + units}}
            cur_chart['plotOptions'] = {}

            charts.append(cur_chart)

    # Volume by day
    # for idx, lift_choice in enumerate(lift_choices):
    #     cur_lift = lifts.filter_by(lift=lift_choice).order_by(asc(LiftEntry.timestamp))

    #     if cur_lift.count() > 0:
    #         oldest_date = cur_lift[0].timestamp.date().toordinal()
    #         cur_date = datetime.utcnow().date().toordinal()
    #         volume = [0 for i in range(cur_date - oldest_date + 1)]

    #         for lift in cur_lift:
    #             day_idx = lift.timestamp.date().toordinal() - oldest_date
    #             volume[day_idx] += lift.weight

    #         cur_chart = {}
    #         cur_chart['chartID'] = 'chart_volume' + str(idx)
    #         cur_chart['chart'] = {"renderTo": 'chartID_' + str(idx), "type": 'column'}
    #         cur_chart['series'] = [{"name": 'Weight', "data": volume}]
    #         cur_chart['chartTitle'] = {"text": "Volume by day: " + lift_choice}
    #         cur_chart['xAxis'] = {"categories": ['D' + str(i) for i in range(len(volume))]}
    #         cur_chart['yAxis'] = {"title": {"text": 'Weight in ' + units}}
    #         cur_chart['plotOptions'] = {}

    #         charts.append(cur_chart)

    # Volume by week
    for idx, lift_choice in enumerate(lift_choices):
        cur_lift = lifts.filter_by(lift=lift_choice).order_by(asc(LiftEntry.timestamp))

        if cur_lift.count() > 0:
            oldest_date = cur_lift[0].timestamp.date().toordinal()
            cur_date = datetime.utcnow().date().toordinal()
            volume = [[0,0,0] for i in range(int((cur_date - oldest_date + 1) / 7))]

            # Three regimes:
            # 75%+, 50%+, and <50%

            # TODO this is garbage performance, should be a SQL query
            maxLift = np.amax([lift.weight for lift in cur_lift])

            for lift in cur_lift:
                day_idx = int((lift.timestamp.date().toordinal() - oldest_date) / 7)
                set_volume = lift.weight * lift.reps
                if lift.weight > 0.75 * maxLift:
                    volume[day_idx][0] += set_volume
                elif lift.weight > 0.5 * maxLift:
                    volume[day_idx][1] += set_volume
                else:
                    volume[day_idx][2] += set_volume

            # TODO: does highcharts work with numpy arrays?
            def col(arr, i):
                return [row[i] for row in arr]

            # TODO: this should be your max at the time, not your current max
            cur_chart = {}
            cur_chart['chartID'] = 'chart_volume_stacked' + str(idx)
            cur_chart['chart'] = {"renderTo": 'chartID_' + str(idx), "type": 'column'}
            cur_chart['series'] = [
                {"name": '75%+ of Max', "data": col(volume, 0)},
                {"name": '50-75% of Max', "data": col(volume, 1)},
                {"name": '0-50% of Max', "data": col(volume, 2)},
                ]
            cur_chart['chartTitle'] = {"text": "Volume by week: " + lift_choice}
            cur_chart['xAxis'] = {"categories": ['W' + str(i) for i in range(len(volume))]}
            cur_chart['yAxis'] = {"title": {"text": 'Weight in ' + units}}
            cur_chart['plotOptions'] = {"series": {"stacking": "normal"}}

            charts.append(cur_chart)

    return render_template('user_analytics.html',
                           title='Analytics',
                           user=user,
                           charts=charts)

@app.route('/user/<username>/workouts')
@login_required
def user_workouts(username):
    user = User.query.filter_by(username=username).first()
    if user == None:
        flash('User %s not found.' % username)
        return redirect(url_for('index'))

    lifts = user.lifts
    units = user.units

    return render_template('user_workouts.html',
                           title='Workouts',
                           user=user,
                           lifts=lifts)

@app.route('/user/<username>/settings', methods=['GET', 'POST'])
@login_required
def user_settings(username):
    # TODO: is this necessary?
    user = User.query.filter_by(username=username).first()
    if user == None:
        flash('User %s not found.' % username)
        return redirect(url_for('index'))

    # TODO: This form is used in multiple places, should be a function
    form = EditForm(g.user.username)
    if form.validate_on_submit():
        g.user.username = form.username.data
        g.user.units = form.units.data
        g.user.sex = form.sex.data
        g.user.about_me = form.about_me.data
        db.session.add(g.user)
        db.session.commit()
        flash('Your changes have been saved.')
        return redirect(url_for('user_settings', username=g.user.username))
    else:
        form.username.data = g.user.username
        form.units.data = g.user.units
        form.sex.data = g.user.sex
        form.about_me.data = g.user.about_me

    return render_template('user_settings.html',
                           title='Settings',
                           user=user,
                           form=form)



@app.route('/signup', methods=['GET', 'POST'])
def signup():
    form = EditForm(g.user.username)
    if form.validate_on_submit():
        g.user.username = form.username.data
        g.user.units = form.units.data
        g.user.sex = form.sex.data
        g.user.about_me = form.about_me.data
        db.session.add(g.user)
        db.session.commit()
        flash('Thanks for registering!')
        return redirect(url_for('index'))
    else:
        form.username.data = g.user.username
        form.units.data = g.user.units
        form.sex.data = g.user.sex
        form.about_me.data = g.user.about_me
    return render_template('signup.html', form=form)


@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html'), 500
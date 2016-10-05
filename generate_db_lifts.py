#!/usr/bin/env python

from app import db, models
import numpy as np
import sys
from datetime import datetime

USERNAME = 'dario_yahoo_dos'

print('If you actually intend to run this, uncomment the sys.exit() line at the start of this file')
sys.exit()

user = models.User.query.filter_by(username=USERNAME).first()
user_id = user.id

# Generate 6 months of data
# shit what does that even look like lol
maxes = {
    'Barbell Squat': [405, 495],
    'Bench Press': [225, 315],
    'Deadlift': [445, 545]
}

warmups = {
    'Barbell Squat': [
        (45, 10), (135, 5), (225, 5), (275, 3)
    ],
    'Bench Press': [
        (45, 10), (95, 8), (135, 5)
    ],
    'Deadlift': [
        (135, 5), (225, 5), (315, 5), (365, 3)
    ]
}

worksets = [0.7, 0.75, 0.8, 0.85, 0.9]

# go back 26 weeks
num_weeks = 26
cur_utc = datetime.utcnow().toordinal()
starting_utc = cur_utc - 7 * num_weeks

for week in range(num_weeks):
    week_utc = starting_utc + week * 7
    alpha = (week + 1) / num_weeks

    for key in maxes:
        week_max = maxes[key][0] + alpha * (maxes[key][1] - maxes[key][0])

        for idx, warmup in enumerate(warmups[key]):
            newLiftEntry = models.LiftEntry()

            newLiftEntry.lift = key
            newLiftEntry.bw = 190
            newLiftEntry.weight = warmup[0]
            newLiftEntry.reps = warmup[1]
            newLiftEntry.rpe = idx
            newLiftEntry.timestamp = datetime.fromordinal(week_utc)
            newLiftEntry.user_id = user_id

            print(newLiftEntry)

            db.session.add(newLiftEntry)
            db.session.commit()

        for workset in worksets:
            # To show volume variance, generate random number of sets
            newLiftEntry = models.LiftEntry()

            newLiftEntry.lift = key
            newLiftEntry.bw = 190
            newLiftEntry.weight = workset * week_max
            newLiftEntry.reps = np.random.randint(1, 10)
            newLiftEntry.rpe = int(10 * workset)
            newLiftEntry.timestamp = datetime.fromordinal(week_utc)
            newLiftEntry.user_id = user_id

            print(newLiftEntry)

            db.session.add(newLiftEntry)
            db.session.commit()

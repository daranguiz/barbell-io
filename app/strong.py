from decimal import *

lb_to_kg = 0.453592

lift_choices = [
    'Barbell Squat',
    'Bench Press',
    'Deadlift',
    'Overhead Press',
    'Upright Row',
    'Pull Up',
    'Dip'
]

def compute_wilks_from_form(wilksForm):
    bw = wilksForm.weight.data

    if wilksForm.sex.data == 'male':
        a = Decimal(-216.0475144)
        b = Decimal( 16.2606339)
        c = Decimal(-0.002388645)
        d = Decimal(-0.00113732)
        e = Decimal( 7.01863E-06)
        f = Decimal(-1.291E-08)
    else:
        a = Decimal( 594.31747775582)
        b = Decimal(-27.23842536447)
        c = Decimal( 0.82112226871)
        d = Decimal(-0.00930733913)
        e = Decimal( 4.731582E-05)
        f = Decimal(-9.054E-08)

    total = Decimal(0.0)
    if wilksForm.squat.data != None:
        total += wilksForm.squat.data
    if wilksForm.bench.data != None:
        total += wilksForm.bench.data
    if wilksForm.deadlift.data != None:
        total += wilksForm.deadlift.data

    if wilksForm.units.data == 'lb':
        bw *= Decimal(lb_to_kg)
        total *= Decimal(lb_to_kg)

    weight_coef = Decimal(500) / (a + b * bw + c * bw**2 + d * bw**3 + e * bw**4 + f * bw**5)

    return weight_coef * total

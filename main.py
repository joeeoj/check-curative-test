#!/usr/bin/env python3
"""Check status of Curative covid test results"""
import json

try:
    import dialogs
    print_instead = False
except ImportError:
    print_instead = True

import arrow
import requests

from config import DOB, TOKEN


BASE_URL = 'https://labtools.curativeinc.com/api/appointments/get_by_access_token/{token}'
TZ = 'America/Los_Angeles'  # default is the west coast but this can be changed to anything


def get_status(token: str, dob: str) -> dict:
    url = BASE_URL.format(token=token)

    r = requests.post(url, json={ 'dob': dob })

    if r.status_code == 200:
        return r.json()
    return None


def localize_time(s: str) -> arrow.arrow.Arrow:
    dt = arrow.get(s)  # assumes ISO format, which is what Curative provides
    return dt.to(TZ)


def human_time(dt: arrow.arrow.Arrow) -> str:
    fmt = 'ddd M/D h:m A'
    return dt.format(fmt)


def hours_elapsed(before: arrow.arrow.Arrow, after: arrow.arrow.Arrow = arrow.now()) -> str:
    # arrow.now() should be local timezone aware
    return before.humanize(after, granularity='hour')


if __name__ == '__main__':
    data = get_status(TOKEN, DOB)

    at_lab = data.get('accessioned_lab')
    testing_started = data.get('in_testing_at')
    results = data.get('appointment_results')

    appt_time = localize_time(data.get('appointment_window').get('start_time'))
    hours_since_test = hours_elapsed(appt_time)
    msg = f'test taken {hours_since_test}\n'

    if at_lab is not None:
        if len(results) > 0:
            test_results = results[0].get('result').upper()

            # recalculate total testing time
            test_completed_time = localize_time(results[0].get('created_at'))

            # if finished change base message with total time
            testing_hours = int((test_completed_time - localize_time(testing_started)).total_seconds() / 60 / 60)
            total_hours = int((test_completed_time - appt_time).total_seconds() / 60 / 60)
            msg = f'test completed after {testing_hours} hours of testing and a total time of {total_hours} hours\n'

            # add results
            msg += 'results: {}'.format(test_results)
        elif testing_started:
            msg += f'testing started on {human_time(localize_time(testing_started))}'
        else:
            received_time = localize_time(data.get('accessioning_package').get('created_at'))
            msg += f'sample in lab on {human_time(received_time)}'
    else:
        msg += 'not sent to lab yet'

    if print_instead:
        print(msg)
    else:
        dialogs.alert(msg)

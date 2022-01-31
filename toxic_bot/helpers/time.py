from datetime import datetime


def time_ago(time1, time2):
    time_diff = time1 - time2
    time_ago_datetime = datetime(1, 1, 1) + time_diff
    time_limit = 0
    time_ago_string = ""
    if time_ago_datetime.year - 1 != 0:
        time_ago_string += "{} Year{} ".format(time_ago_datetime.year - 1, determine_plural(time_ago_datetime.year - 1))
        time_limit += 1
    if time_ago_datetime.month - 1 != 0:
        time_ago_string += "{} Month{} ".format(time_ago_datetime.month - 1, determine_plural(time_ago_datetime.month - 1))
        time_limit += 1
    if time_ago_datetime.day - 1 != 0 and not time_limit == 2:
        time_ago_string += "{} Day{} ".format(time_ago_datetime.day - 1, determine_plural(time_ago_datetime.day - 1))
        time_limit += 1
    if time_ago_datetime.hour != 0 and not time_limit == 2:
        time_ago_string += "{} Hour{} ".format(time_ago_datetime.hour, determine_plural(time_ago_datetime.hour))
        time_limit += 1
    if time_ago_datetime.minute != 0 and not time_limit == 2:
        time_ago_string += "{} Minute{} ".format(time_ago_datetime.minute, determine_plural(time_ago_datetime.minute))
        time_limit += 1
    if not time_limit == 2:
        time_ago_string += "{} Second{} ".format(time_ago_datetime.second, determine_plural(time_ago_datetime.second))
    return time_ago_string


def determine_plural(number):
    if int(number) != 1:
        return 's'
    else:
        return ''

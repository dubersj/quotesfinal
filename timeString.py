from datetime import datetime

def timeString():
    current_time = datetime.now()

    # make minutes display correctly
    if len(str(current_time.minute)) == 1:
        minute = str(current_time.minute)
        minute = "0" + minute
    else:
        minute = str(current_time.minute)

    saved_date = str(current_time.month) + '/' + str(current_time.day) + '/' + str(current_time.year)
    saved_time = str(current_time.hour) + ':' + minute + "UTC"
    saved_datetime_string = saved_date + ' ' + saved_time
    return saved_datetime_string

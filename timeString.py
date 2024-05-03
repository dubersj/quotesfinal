from datetime import datetime

def timeString():
    current_time = datetime.now()
    saved_date = str(current_time.month) + '/' + str(current_time.day) + '/' + str(current_time.year)
    saved_time = str(current_time.hour) + ':' + str(current_time.minute) + "UTC"
    saved_datetime_string = saved_date + ' ' + saved_time
    return saved_datetime_string
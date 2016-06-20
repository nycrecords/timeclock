from datetime import datetime
def get_day_of_week():
    date_int_to_str = {
        0: "Monday",
        1: "Tuesday",
        2: "Wednesday",
        3: "Thursday",
        4: "Friday",
        5: "Saturday",
        6: "Sunday"
    }
    return date_int_to_str[datetime.today().weekday()]
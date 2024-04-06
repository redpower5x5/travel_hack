from datetime import datetime, timedelta

def get_next_week_dates(given_date):
    # Find out the day of the week (0=Monday, 6=Sunday)
    day_of_week = given_date.weekday()

    # Calculate the start of the next week (next Monday)
    # If the given day is Monday, we need to add 7 days to get to the next Monday
    days_till_next_monday = 7 - day_of_week
    start_of_next_week = given_date + timedelta(days=days_till_next_monday)

    # End of the next week (next Sunday) is 6 days after the start of the week
    end_of_next_week = start_of_next_week + timedelta(days=6)

    # Return the dates as strings
    return start_of_next_week, end_of_next_week
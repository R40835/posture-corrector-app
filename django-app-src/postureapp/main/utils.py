from main.models import Notifications
import datetime


# utility functions to calulate the statistics and time
def get_latest_notifications(user: object) -> dict:
    notifications = Notifications.objects.filter(subject=user)
    latest_notifications = {'back_alert': 0, 'neck_alert': 0}
    for notification in notifications:
        latest_notifications['back_alert'] += notification.back_alert
        latest_notifications['neck_alert'] += notification.neck_alert
    return latest_notifications


def compute_posture_score(total_time: int, num_alerts: int) -> int:
    poor_posture_time = num_alerts * 10
    poor_posture_percentage = poor_posture_time / total_time * 100
    posture_score = 100 - poor_posture_percentage
    return posture_score


def good_posture_time(total_time: int, total_alerts: int) -> int:
    return total_time - total_alerts * 10


def current_time(time_seconds: int) -> datetime.datetime:
    return datetime.datetime.fromtimestamp(time_seconds)


def format_time(seconds):
    if seconds < 60:
        return f'{seconds} seconds'
    elif seconds < 3600:
        minutes = seconds // 60
        seconds = seconds % 60
        return f'{minutes} minutes and {seconds} seconds'
    else:
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        seconds = seconds % 60
        return f'{hours} hours, {minutes} minutes and {seconds} seconds'
    

def overall_improvement(scores):
    if len(scores) < 2:
        return 0
    
    first_score = scores[-2]
    last_score = scores[-1]
    improvement = last_score - first_score
    improvement_percentage = (improvement / first_score) * 100
    
    return round(improvement_percentage, 2)


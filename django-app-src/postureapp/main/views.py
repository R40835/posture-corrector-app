from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render
from .forms import LoginForm, RegisterForm, FeedBackForm
from django.http import HttpResponseRedirect, HttpResponse
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import User, Notifications, Videos, FeedBack, PoorPostures
from django.utils.timezone import now
from main.utils import get_latest_notifications, compute_posture_score, \
good_posture_time, current_time, format_time, overall_improvement
from django.db.models import Sum, Avg, Max
from datetime import datetime
import json


# uploading incorrect posture photos from Jetson Nano
@csrf_exempt
def upload_posture_photos(request):
    if request.method == 'POST':
        # Get the uploaded files from the request
        user = authenticate(request, email=request.POST.get('email'), password=request.POST.get('password'))
        files = request.FILES.getlist('image')

        # Process the uploaded files
        if files:
            for file in files:
                # Create a new PoorPostures object and assign the uploaded file
                posture = PoorPostures(
                    subject = user,
                    posture_photo = file
                )
                
                posture.save()

            # Return a response indicating success
            return HttpResponse('Files uploaded successfully.')
        else:
            # Return a response indicating failure
            return HttpResponse('No files uploaded.')
    else:
        # Return a response indicating invalid method
        return HttpResponse('Invalid request method.')


# receiving all postures adopted and related data during the monitoring video
@csrf_exempt
def video_data(request):
    if request.method == 'POST':
        print('working here...')
        data = request.POST.dict()  # get the dictionary of data sent in the request
        user = authenticate(request, email=request.POST.get('email'), password=request.POST.get('password'))
        # get user
        user = User.objects.get(email=user)
        # loading list of incorrect postures
        incorrect_postures = json.loads(data['incorrect_postures'])
        start_time = int(data['start_time'])
        end_time = int(data['end_time'])
        num_alerts = int(data['total_alerts'])
        # in seconds
        total_time = end_time - start_time
        # start and end time in date time format
        start_time = current_time(start_time)
        end_time = current_time(end_time)
        print(start_time, end_time)
        # calulate posture score
        posture_score = compute_posture_score(total_time=total_time, num_alerts=num_alerts)
        # populating database
        new_video = Videos(
                    subject=user, 
                    start_time=start_time, 
                    end_time=end_time, 
                    total_time_seconds=total_time,
                    total_alerts=num_alerts, 
                    incorrect_postures=incorrect_postures, 
                    posture_score=posture_score
                    )
        new_video.save()
        return JsonResponse({'status': 'success'})
    else:
        return JsonResponse({'status': 'error', 'message': 'Invalid request method'})
    

# authentificating user on jetson nano when they start using the camera
@csrf_exempt
def identify_camera(request):
    if request.method == 'POST':
        user = authenticate(request, email=request.POST.get('email'), password=request.POST.get('password'))
        if user:
            return JsonResponse({'status': 'user identified'})
        else:
            return JsonResponse({'status': 'incorrect email or password'})


# receiving notifications from jetson nano and updating database
@csrf_exempt
def my_endpoint(request): 
    if request.method == 'POST':
        data = request.POST.dict()  # get the dictionary of data sent in the request
        user = authenticate(request, email=request.POST.get('email'), password=request.POST.get('password'))
        user = User.objects.get(email=user)
        notification = Notifications.objects.get(subject=user)
        if data['alert'] == 'back':
            notification.back_alert += 1
            notification.save()
        elif data['alert'] == 'neck':
            notification.neck_alert += 1
            notification.save()
        return JsonResponse({'status': 'success'})
    else:
        return JsonResponse({'status': 'error', 'message': 'Invalid request method'})


# welcome page
def index(request):
    feedbacks = FeedBack.objects.order_by('-date_created')[:2]
    context = {'feedbacks': feedbacks}
    return render(request, 'main/index.html', context)


# sign up page
def register_view(request):
    if request.method == 'POST':
        # handling data posted as well as files such as pictures
        form = RegisterForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.save()
            login(request, user)
            # reverse checkse the url name most specify the app as well
            return HttpResponseRedirect(reverse('main:home_view'))
    else:
        form = RegisterForm()
    return render(request, 'main/register.html', {'form': form})


# login page
def login_view(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data.get('email')
            password = form.cleaned_data.get('password')
            user = authenticate(email=email, password=password)
            if user is not None:
                login(request, user)
                # display message account created
                return HttpResponseRedirect(reverse('main:home_view'))
    else:
        form = LoginForm()
        # works just sort out reverse
    return render(request, 'main/login.html', {'form': form})

# authenticated users' pages:
# home page 
@login_required
def home_view(request):
    # change it to user first name later on
    user = request.user
    context = {'user': user}
    print(request.user)
    return render(request, 'main/home.html', context)


# logout button
@login_required
def user_logout(request):
    print(request.user.id)
    logout(request)
    # messages.success(request, 'user logged out successfully')
    return HttpResponseRedirect(reverse('index'))


# profile page: render user details and statistics
@login_required
def user_profile(request):
    # get user
    user = User.objects.get(pk=request.user.id) 

    # days on app
    days_in_app = (now() - user.date_created).days
    # get the video details:    
    # get time spent in a good posture
    try:
        # sum all user's alerts for each video
        total_alerts = Videos.objects.filter(subject=user).aggregate(Sum('total_alerts'))['total_alerts__sum']
        # sum all user's total time for each video
        total_time = Videos.objects.filter(subject=user).aggregate(Sum('total_time_seconds'))['total_time_seconds__sum']
        # compute good posture time
        good_posture = good_posture_time(total_time=total_time, total_alerts=total_alerts)
        good_posture = format_time(good_posture)
    except:
        # if video does not exist
        good_posture = 0
    # get the latest video score
    latest_video = Videos.objects.filter(subject=user).order_by('-end_time').first()
    if latest_video:
        # If there's a latest video, get its posture score
        latest_score = latest_video.posture_score
    else:
        # If there's no video for the current user, set the latest posture score to 0
        latest_score = 0
    # Get the average posture score of all videos for the user
    average_score = Videos.objects.filter(subject=user).aggregate(Avg('posture_score'))['posture_score__avg']
    # If there are no videos for the user, set the average posture score to 0
    if not average_score:
        average_score = 0
    else:
        average_score = round(average_score, 2)


    highest_score = Videos.objects.filter(subject=user).aggregate(Max('posture_score'))['posture_score__max']

    if not highest_score:
        highest_score = 0
    
    # posture improvements:
    videos = Videos.objects.filter(subject=request.user).order_by('start_time')
    scores = [video.posture_score for video in videos]
    improvement = overall_improvement(scores)

    context = {
        'user': user,
        'good_postures': good_posture,
        'days_in_app': days_in_app,
        'latest_score': latest_score,
        'average_score': average_score,
        'highest_score': highest_score,
        'improvement': improvement,
            }
    
    return render(request, 'main/profile.html', context)


# feedback post page
@login_required
def user_feedback(request):
    if request.method == 'POST':
        # handling data posted as well as files such as pictures
        form = FeedBackForm(request.POST)
        if form.is_valid():
            feedback = form.save(commit=False)
            feedback.author = request.user
            feedback.save()
            return HttpResponseRedirect(reverse('main:home_view'))
    else:
        form = FeedBackForm()
    context = {'form': form}
    return render(request, 'main/feedback.html', context)


# History Page
@login_required
def user_record(request):
    user = request.user
    # querying database for videos details
    videos = Videos.objects.filter(subject=user).order_by('end_time')[::-1]
    context = {'videos': videos}
    return render(request, 'main/record.html', context)


# search bar
@login_required
def search_records(request):
    if request.method == 'POST':
        start_date_str = request.POST['searched']
        current_user = request.user
        print(start_date_str)
        if start_date_str is not None:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            start_datetime = datetime.combine(start_date, datetime.min.time())
            end_datetime = datetime.combine(start_date, datetime.max.time())
            videos = Videos.objects.filter(
                subject=current_user,
                start_time__range=(start_datetime, end_datetime)
            )

        else:
            videos = Videos.objects.filter(subject=current_user)

        context = {
            'videos': videos,
        }
        return render(request, 'main/search.html', context)
    else:
        return render(request, 'main/search.html')


# incorrect posture photos feed
@login_required
def posture_photos(request):
    user = request.user
    photos = PoorPostures.objects.filter(subject=user).order_by('date_created')[::-1]
    context = {'photos': photos}
    return render(request, 'main/photos.html', context)


# establishing SSE connection
@login_required
def sse(request):
    response = HttpResponse(content_type='text/event-stream')
    response['Cache-Control'] = 'no-cache'
    response['Connection'] = 'keep-alive'

    notifications = get_latest_notifications(request.user)
    data = json.dumps({'back_alert': notifications['back_alert'], 'neck_alert': notifications['neck_alert']})
    response.write(f"data: {data}\n\n")
    return response


# posture monitoring page: notifications will be displayed here
@login_required
def user_monitoring(request):
    user_id = request.user.id
    notifications = Notifications.objects.get(subject_id=user_id)
    return render(request, 'main/monitoring.html', {'back_postures': notifications.back_alert})
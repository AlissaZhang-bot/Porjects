##====================================================================
# This is our main backend
# Each function with parameter "request" to receive data from frontend
# and return a response
##====================================================================

from django.core.files.storage import default_storage
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import render
from django.urls import reverse
from django.http import HttpResponse, HttpResponseRedirect
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from .models import Account, Accommodation, AccommodationAlbum, Amenity, Share_space, Review, Request, Order, Comment, UserHistory, RequestReview, RequestComment, ReviewsAlbum
from .utils import gen_token, get_username_by_session, generate_filename, get_basic_nums_at_profile, formalize_latlng, hide_card_number, trans_latlng_and_address, save_history, recommend
from .update_db import update_accommodation_info, modify_location, modify_album_url, set_guests_bedrooms_num
from google.cloud import storage
from geopy.distance import geodesic
import base64
import datetime
import time
import json
import pytz

##========================================
# This signiture used to encrypt the data
# when store the data into cookies
##========================================
salt_signiture = "asdasd"

##========================================
# Set the current timezone in Sydney
##========================================
tz = pytz.timezone('Australia/Sydney')


##========================================
# Index function is to present our homepage
# to users, including recommender results 
# and TopK list.
##========================================
def index(request):
    # Get username from session
    username = get_username_by_session(request)
    # Get basic data of current user
    data = get_basic_nums_at_profile(request)
    # If user has login
    if username:
        # Get user object
        account = Account.objects.get(username=username)
        recommends = []
        # Get the results from recommend function in utils.py
        for e in recommend(request):
            recommends.append(Accommodation.objects.get(id=int(e)))
        # Construct data for frontend
        data['recommends'] = recommends
        data['likes'] = UserHistory.objects.filter(owner_id=account).filter(is_favourite=True).values_list('accommodation_id', flat=True)
        data['topK'] = Accommodation.objects.all().order_by("avg_rating").reverse()[:20]
    else:
        # If user has not login
        recommends = []
        for e in recommend(request):
            recommends.append(Accommodation.objects.get(id=int(e)))
        # Construct data for frontend
        data['recommends'] = recommends
        # There is no favorite data if user has not login
        data['likes'] = []
        data['topK'] = Accommodation.objects.all().order_by("avg_rating").reverse()[:20]
    return render(request, 'index.html', data)

##========================================
# This function is to get the requests list
##========================================
def request_listings(request):
    # Get basic data of current user
    data = get_basic_nums_at_profile(request)
    page = request.GET.get('page')
    if not page:
        page = 1
    else:
        page = int(page)
    if request.method == "GET":
        user_requests = Request.objects.filter(is_public=True)
        # add paginator
        try:
            paginator = Paginator(user_requests, 10)
            listings_on_page = paginator.page(page)
            data["user_requests"] = listings_on_page.object_list
            data["nb_of_pages"] = paginator.num_pages
            data["has_previous"] = listings_on_page.has_previous()
            data["has_next"] = listings_on_page.has_next()
            data["page_range"] = paginator.page_range
        except EmptyPage:
            data["has_previous"] = False
            data["has_next"] = False
            data["page_range"] = (1,2)
            data["user_requests"] = listings_on_page.object_list
            data["nb_of_pages"] = 1
        data["request_type"] = "ALL"
        data["curr_page"] = page
        data["previous_page"] = page - 1
        data["next_page"] = page + 1
    return render(request, 'request-listing.html', data)

##===================================
# This function is to record user's 
# favorite accommodations
##===================================
def favourite(request):
    print('[INFO] Favourite Function')
    # Get username from session
    username = get_username_by_session(request)
    # If user has login
    if username:
        # Get basic data of current user
        data = get_basic_nums_at_profile(request)
        # Get the parameter accommodation ID from GET request of frontend
        acc_id = request.GET.get('acc_id','')
        accommodation = Accommodation.objects.get(id=int(acc_id))
        # Record this accommodation using save_history function
        save_history(username, accommodation, 'favourite')
        account = Account.objects.get(username=username)
        listings = Accommodation.objects.filter(owner_id=account)
        data['account'] = account
        data['listings'] = listings[:3]
        data['liked'] = UserHistory.objects.filter(owner_id=account).filter(is_favourite=True).select_related('accommodation_id').order_by('time').reverse()
        data['likes'] = UserHistory.objects.filter(owner_id=account).filter(is_favourite=True).values_list('accommodation_id', flat=True)
        history = UserHistory.objects.filter(owner_id=account).filter(is_history=True).select_related('accommodation_id').order_by('time').reverse()
        data['history'] = history
        return render(request, 'author-single.html', data)
    return HttpResponseRedirect(reverse('index')) 

##===================================
# This function is to record user's 
# unfavorite accommodations
##===================================
def undo(request):
    print('[INFO] Undo function')
    # Get username from session
    username = get_username_by_session(request)
    if username:
        # Get basic data of current user
        data = get_basic_nums_at_profile(request)
        # Get the parameter accommodation ID from GET request of frontend
        acc_id = request.GET.get('acc_id','')
        accommodation = Accommodation.objects.get(id=int(acc_id))
        # Record it using save_history function
        save_history(username, accommodation, 'undo')
        account = Account.objects.get(username=username)
        listings = Accommodation.objects.filter(owner_id=account)
        data['account'] = account
        data['listings'] = listings[:3]
        data['liked'] = UserHistory.objects.filter(owner_id=account).filter(is_favourite=True).select_related('accommodation_id').order_by('time').reverse()
        data['likes'] = UserHistory.objects.filter(owner_id=account).filter(is_favourite=True).values_list('accommodation_id', flat=True)
        history = UserHistory.objects.filter(owner_id=account).filter(is_history=True).select_related('accommodation_id').order_by('time').reverse()
        data['history'] = history
        return render(request, 'author-single.html', data)
    return HttpResponseRedirect(reverse('index'))

##===================================
# This function is to fetch data of 
# user profile, including basic data, 
# favorite list and history list
##===================================
def user_profile(request):
    # Get basic data of current user
    data = get_basic_nums_at_profile(request)
    # Get the parameter username from GET request of frontend
    account_username = request.GET.get('account_username','')
    account = Account.objects.get(username=account_username)
    listings = Accommodation.objects.filter(owner_id=account)
    data['account'] = account
    data['listings'] = listings
    data['liked'] = UserHistory.objects.filter(owner_id=account).filter(is_favourite=True).select_related('accommodation_id').order_by('time').reverse()
    data['likes'] = UserHistory.objects.filter(owner_id=account).filter(is_favourite=True).values_list('accommodation_id', flat=True)
    history = UserHistory.objects.filter(owner_id=account).filter(is_history=True).select_related('accommodation_id').order_by('time').reverse()
    data['history'] = history
    
    return render(request, 'author-single.html', data)

##===================================
# This function is to fetch data of 
# requests that are public
##===================================
@csrf_exempt
def user_active_request(request):
    # Get basic data of current user
    data = get_basic_nums_at_profile(request)
    username = get_username_by_session(request)
    page = request.GET.get('page')
    if not page:
        page = 1
    else:
        page = int(page)
    if request.method == "GET":
        if username:
            user = Account.objects.get(username=username)
            my_request = Request.objects.filter(owner_id=user).filter(is_public=True)
            # Add paginator
            try:
                paginator = Paginator(my_request, 10)
                listings_on_page = paginator.page(page)
                data["user_requests"] = listings_on_page.object_list
                data["nb_of_pages"] = paginator.num_pages
                data["has_previous"] = listings_on_page.has_previous()
                data["has_next"] = listings_on_page.has_next()
                data["page_range"] = paginator.page_range
            except EmptyPage:
                data["has_previous"] = False
                data["has_next"] = False
                data["page_range"] = (1,2)
                data["user_requests"] = listings_on_page.object_list
                data["nb_of_pages"] = 1
            data["request_type"] = "Active"
            data["curr_page"] = page
            data["previous_page"] = page - 1
            data["next_page"] = page + 1
        return render(request, "dashboard-request-table.html", data)

##===================================
# This function is to fetch data of 
# requests that are pedding
##===================================
@csrf_exempt
def user_pending_request(request):
    # Get basic data of current user
    data = get_basic_nums_at_profile(request)
    username = get_username_by_session(request)
    page = request.GET.get('page')
    if not page:
        page = 1
    else:
        page = int(page)
    if request.method == "GET":
        if username:
            user = Account.objects.get(username=username)
            my_request = Request.objects.filter(owner_id=user).filter(is_public=False)
             # add paginator
            try:
                paginator = Paginator(my_request, 10)
                listings_on_page = paginator.page(page)
                data["user_requests"] = listings_on_page.object_list
                data["nb_of_pages"] = paginator.num_pages
                data["has_previous"] = listings_on_page.has_previous()
                data["has_next"] = listings_on_page.has_next()
                data["page_range"] = paginator.page_range
            except EmptyPage:
                data["has_previous"] = False
                data["has_next"] = False
                data["page_range"] = (1,2)
                data["user_requests"] = listings_on_page.object_list
                data["nb_of_pages"] = 1
            data["request_type"] = "Pending"
            data["curr_page"] = page
            data["previous_page"] = page - 1
            data["next_page"] = page + 1
    return render(request, "dashboard-request-table.html", data)

##=======================================
# This function is to archive this request
##=======================================
@csrf_exempt
def archiveRequest(request):
    if request.method == "GET":
        request_id = request.GET.get('request_id','')
        if request_id:
            Request.objects.filter(id = int(request_id)).update(is_public=False)
        curr_url = request.path
        parent_url = curr_url.rsplit('/',2)[0]
        if parent_url == "/user_request_active":
            return HttpResponseRedirect(reverse('user_active_request'))
        elif parent_url == "/user_request_pending":
            return HttpResponseRedirect(reverse('user_pending_request'))
        return HttpResponseRedirect(reverse('user_requests'))

##=======================================
# This function is to public this request
##=======================================
@csrf_exempt
def publicRequest(request):
    if request.method == "GET":
        request_id = request.GET.get('request_id','')
        if request_id:
            Request.objects.filter(id = int(request_id)).update(is_public=True)
        curr_url = request.path
        parent_url = curr_url.rsplit('/',2)[0]
        if parent_url == "/user_request_active":
            return HttpResponseRedirect(reverse('user_active_request'))
        elif parent_url == "/user_request_pending":
            return HttpResponseRedirect(reverse('user_pending_request'))
        return HttpResponseRedirect(reverse('user_requests'))

##=======================================
# This function is to search all requests
# that are meet search conditions
##=======================================
def search_requests(request):
    # Get basic data of current user
    data = get_basic_nums_at_profile(request)
    page = request.GET.get('page')
    if not page:
        page = 1
    else:
        page = int(page)
    city = request.GET.get('city','')
    if not city:
        city = 'Sydney'
    
    adults_quantity = request.GET.get('adults_quantity','')
    rooms_quantity = request.GET.get('rooms_quantity','')
    ret = []
    filtered_requests = Request.objects.filter(is_public=True, city=city, guests_num__gte = adults_quantity, bedrooms_num__gte = rooms_quantity)
    # Add paginator
    try:
        paginator = Paginator(filtered_requests, 10)
        listings_on_page = paginator.page(page)
        data["user_requests"] = listings_on_page.object_list
        data["nb_of_pages"] = paginator.num_pages
        data["has_previous"] = listings_on_page.has_previous()
        data["has_next"] = listings_on_page.has_next()
        data["page_range"] = paginator.page_range
    except EmptyPage:
        data["has_previous"] = False
        data["has_next"] = False
        data["page_range"] = (1,2)
        data["user_requests"] = listings_on_page.object_list
    data["nb_of_pages"] = 1
    data["curr_page"] = page
    data["previous_page"] = page - 1
    data["next_page"] = page + 1

    data['city'] = city
    data['adults_quantity'] = adults_quantity
    data['rooms_quantity'] = rooms_quantity
    data['current_path'] = request.get_full_path()
    data["user_requests"] = filtered_requests
    return render(request, 'request-listing.html', data)

##=======================================
# This function is to list all requests 
# of current user
##=======================================
@csrf_exempt
def user_requests(request):
    page = request.GET.get('page')
    if not page:
        page = 1
    else:
        page = int(page)
    # Get basic data of current user
    data = get_basic_nums_at_profile(request)
    username = get_username_by_session(request)
    if request.method == "GET":
        if username:
            user = Account.objects.get(username=username)
            user_requests = Request.objects.filter(owner_id=user)
            data["user_requests"] = user_requests
            # Add paginator
            try:
                paginator = Paginator(user_requests, 10)
                listings_on_page = paginator.page(page)
                data["user_requests"] = listings_on_page.object_list
                data["nb_of_pages"] = paginator.num_pages
                data["has_previous"] = listings_on_page.has_previous()
                data["has_next"] = listings_on_page.has_next()
                data["page_range"] = paginator.page_range
            except EmptyPage:
                data["has_previous"] = False
                data["has_next"] = False
                data["page_range"] = (1,2)
                data["user_requests"] = listings_on_page.object_list
                data["nb_of_pages"] = 1
            data["request_type"] = "ALL"
            data["curr_page"] = page
            data["previous_page"] = page - 1
            data["next_page"] = page + 1
        return render(request, "dashboard-request-table.html", data)

##=======================================
# This function is to show user request 
##=======================================
def request_single(request):
    # Get basic data of current user
    data = get_basic_nums_at_profile(request)
    username = get_username_by_session(request)
    if request.method == "GET":
        request_id = request.GET.get('request_id','')
        ret = Request.objects.get(id = int(request_id)) # set parameter
        reviews = RequestReview.objects.filter(request_id=request_id)
        reviews_count = len(reviews)
        rw_comments = []
        for rw in reviews:
            rw_comments += RequestComment.objects.filter(request_id=rw.id).select_related('username','reply_to','request_id').order_by('comment_time').reverse()
        data['ret'] = ret
        data['reviews'] = reviews
        data['reviews_count'] = reviews_count
        data['rw_comments'] = rw_comments
        return render(request, "request-single.html", data)

##=======================================
# This function is to put or edit user request 
##=======================================
@csrf_exempt
def request(request):
    # Get basic data of current user
    data = get_basic_nums_at_profile(request)
    # When user want to edit, we load data of this request first
    if request.method == "GET":
        request_id = request.GET.get('request_id','')
        if request_id:
            request_id = int(request_id)
            ret = Request.objects.filter(id = request_id)
            if len(ret) > 0:
                data['request_id'] = json.dumps(ret[0].id)
                data["request_title"] = ret[0].title
                data['request_type'] = ret[0].property_type
                data['city'] = ret[0].city
                data['description'] = ret[0].description
                data['geust_num'] = json.dumps(ret[0].guests_num)
                data['beds_num'] = json.dumps(ret[0].beds_num)
                data['bedrooms_num'] = json.dumps(ret[0].bedrooms_num)
                data['bathrooms_num'] = json.dumps(ret[0].bathrooms_num)
                data['wifi'] = ret[0].wifi
                data['air_conditioning'] = ret[0].air_conditioning
                data['tv'] = ret[0].tv
                data['parking'] = ret[0].parking
                data['fitness'] = ret[0].gym
        return render(request, 'request.html', data)
    if request.method == "POST":
        check_type = {'true': True, 'false': False, '': False}
        title = request.POST.get('title','')
        type_ = request.POST.get('type','')
        city = request.POST.get('city','')
        description = request.POST.get('description','')
        bedroom = request.POST.get('bedroom','')
        bed = request.POST.get('bed','')
        geust = request.POST.get('geust','')
        bathroom = request.POST.get('bathroom','')
        
        wifi = check_type[request.POST.get('wifi','')]
        parking = check_type[request.POST.get('parking','')]
        fitness = check_type[request.POST.get('fitness','')]
        washing_machine = check_type[request.POST.get('washing_machine','')]
        air_conditioning = check_type[request.POST.get('air_conditioning','')]
        tv = check_type[request.POST.get('tv','')]
        request_id = request.POST.get('request_id','')
        if request_id:
            request_id = int(request_id)
            Request.objects.filter(id = request_id).update(
                title = title,
                property_type = type_,
                city = city,
                description = description,
                guests_num = geust,
                bedrooms_num = bedroom,
                beds_num = bed,
                bathrooms_num = bathroom,
                tv = tv,
                wifi = wifi,
                air_conditioning = air_conditioning,
                parking = parking,
                washing_machine = washing_machine,
                gym = fitness,
            )
            data['request_id'] = json.dumps(request_id)
        else:
            username = get_username_by_session(request)
            owner_id = Account.objects.get(username=username)
            try:
                request = Request(
                    owner_id = owner_id,
                    title = title,
                    description = description,
                    property_type = type_,
                    city = city,
                    guests_num = geust,
                    bedrooms_num = bedroom,
                    beds_num = bed,
                    bathrooms_num = bathroom,
                    tv = tv,
                    wifi = wifi,
                    air_conditioning = air_conditioning,
                    parking = parking,
                    washing_machine = washing_machine,
                    gym = fitness,
                )
                request.save()
            except ValueError:
                data['status'] = 'fail'
                return JsonResponse(data)
            else:
                request_id = request.id
                data['request_id'] = json.dumps(request_id)
        data['status'] = 'succeed'
        return JsonResponse(data)

##========================================
# Delete accommodation image that user 
# choose, and delete the image from cloud
# at the same time update the database.
##========================================
@csrf_exempt
def delete_photo(request):
    if request.method == "POST":
        data = get_basic_nums_at_profile(request)
        username = get_username_by_session(request)
        owner_id = Account.objects.get(username=username)
        img_raw = request.POST.get('img')
        acc_id = request.POST.get('acc_id')
        acc_id = int(acc_id)
        print('delete: ', acc_id, img_raw)
        img = img_raw.replace("https://storage.cloud.google.com/accomodation9900_property_images/","")
        storage_client = storage.Client.from_service_account_json("backend/Accommodation9900Storage-449e7001109e.json")
        bucket = storage_client.get_bucket('accomodation9900_property_images')

        blob = bucket.blob(img)
        blob.delete()
        acc_album = AccommodationAlbum.objects.using('db1').filter(accommodation_id=acc_id)
        if acc_album.count() == 1:
            acc_album = AccommodationAlbum.objects.using('db1').get(accommodation_id=acc_id)
            urls_str = acc_album.urls.replace("'",'"')
            urls_list = json.loads(urls_str)
            if img_raw in urls_list:
                urls_list.pop(urls_list.index(img_raw)) 
            acc_album.urls = urls_list
            acc_album.save(using='db1')

        return JsonResponse(data) 

##========================================
# Save the accommodation image and upload 
# it to google cloud, at same time save 
# the image url into database, and update 
# accommodation data
##========================================
@csrf_exempt
def upload_photo(request):
    if request.method == "POST":
        data = get_basic_nums_at_profile(request)
        username = get_username_by_session(request)
        owner_id = Account.objects.get(username=username)
        acc_id = request.POST.get('acc_id','')

        ###############################
        ### Read image data from frontend and extract the data in base64 format
        img_content = request.POST.get('img', '').split(',')[1]
        img = base64.b64decode(img_content)
        file_name = generate_filename("posting", '.jpg') # Give each file a uniq name in cloud storage
        ###############################

        ###############################
        ### Upload image to google cloud
        file = default_storage.open(file_name, 'w')
        file.write(img)
        file.close()
        ###############################

        data['img_url'] = 'https://storage.cloud.google.com/accomodation9900_property_images/'+file_name
        if acc_id:
            Accommodation.objects.filter(id = int(acc_id)).update(
                album_address = data['img_url']
            )
            data['acc_id'] = json.dumps(int(acc_id))
        else:
            accommodation = Accommodation(
                owner_id = owner_id,
                album_address = data['img_url']
            )
            accommodation.save()
            acc_id = accommodation.id
            amenity = Amenity(
                accommodation_id = accommodation
            )
            share_space = Share_space(
                accommodation_id = accommodation
            )
            amenity.save()
            share_space.save()
            data['acc_id'] = json.dumps(int(acc_id))                    
        return JsonResponse(data)

##=================================================================
# According to input from user to search the related accommodation, 
# user may also add more filters.
##=================================================================
def listing(request):
    data = get_basic_nums_at_profile(request)
    city = request.GET.get('city','')
    page = request.GET.get('page')
    if not page:
        page = 1
    else:
        page = int(page)
    
    ###############################
    ### filters for searching
    if not city:
        city = 'Sydney'
    latitude, longitude = trans_latlng_and_address(city, 'address_to_latlng')
    data['lat'] = latitude
    data['lng'] = longitude
    loc_city = trans_latlng_and_address('('+str(latitude)+','+str(longitude)+')', 'get_suburb')

    data['date'] = ""
    date = request.GET.get('date','')
    adults_quantity = request.GET.get('adults_quantity','')
    rooms_quantity = request.GET.get('rooms_quantity','')
    ret = []
    accommodations = Accommodation.objects.filter(city=loc_city, guests_num__gte = adults_quantity, bedrooms_num__gte = rooms_quantity, is_public=True)
    
    if date:
        data['date'] = date
        dates = date.replace(" ","").split("-")
        dates[0] = '-'.join(list(reversed(dates[0].split("/"))))
        dates[1] = '-'.join(list(reversed(dates[1].split("/"))))
        check_in_date = datetime.datetime.strptime(dates[0],'%Y-%d-%m')
        check_out_date = datetime.datetime.strptime(dates[1],'%Y-%d-%m')
        orders = Order.objects.filter(check_in__lt=check_out_date, check_out__gt=check_in_date, status__in=['not paid yet', 'paid', 'finished'])
        occupied_acc = []
        for order in orders:
            o_acc_id = order.accommodation_id.id
            if order.status == 'not paid yet' and (datetime.datetime.now(tz) - order.order_time).seconds > 1800:
                order.status = 'canceled'
                order.save()
            if o_acc_id not in occupied_acc:
                occupied_acc.append(o_acc_id)
        accommodations = accommodations.exclude(id__in = occupied_acc)
    ###############################

    ###############################
    # Accommodation extra filter on listing page
    isAirconditioning = request.GET.get('isAirconditioning')
    if isAirconditioning:
        temp_acc_id = []
        data['isAirconditioning'] = isAirconditioning
        for a in accommodations:
            if Amenity.objects.filter(accommodation_id=a, air_conditioning=True):
                temp_acc_id.append(a.id)
        accommodations = Accommodation.objects.filter(id__in=temp_acc_id)
    
    isHeat = request.GET.get('isHeat')
    if isHeat:
        temp_acc_id = []
        data['isHeat'] = isHeat
        for a in accommodations:
            if Amenity.objects.filter(accommodation_id=a, heat=True):
                temp_acc_id.append(a.id)
        accommodations = Accommodation.objects.filter(id__in=temp_acc_id)
    
    isHairdryer = request.GET.get('isHairdryer')
    if isHairdryer:
        temp_acc_id = []
        data['isHairdryer'] = isHairdryer
        for a in accommodations:
            if Amenity.objects.filter(accommodation_id=a, hair_dryer=True):
                temp_acc_id.append(a.id)
        accommodations = Accommodation.objects.filter(id__in=temp_acc_id)
    
    isTV = request.GET.get('isTV')
    if isTV:
        temp_acc_id = []
        data['isTV'] = isTV
        for a in accommodations:
            if Amenity.objects.filter(accommodation_id=a, tv=True):
                temp_acc_id.append(a.id)
        accommodations = Accommodation.objects.filter(id__in=temp_acc_id)
    
    isWifi = request.GET.get('isWifi')
    if isWifi:
        temp_acc_id = []
        data['isWifi'] = isWifi
        for a in accommodations:
            if Amenity.objects.filter(accommodation_id=a, wifi=True):
                temp_acc_id.append(a.id)
        accommodations = Accommodation.objects.filter(id__in=temp_acc_id)

    isgym = request.GET.get('isgym')
    if isgym:
        temp_acc_id = []
        data['isgym'] = isgym
        for a in accommodations:
            if Share_space.objects.filter(accommodation_id=a, gym=True):
                temp_acc_id.append(a.id)
        accommodations = Accommodation.objects.filter(id__in=temp_acc_id)
    
    isParking = request.GET.get('isParking')
    if isParking:
        temp_acc_id = []
        data['isParking'] = isParking
        for a in accommodations:
            if Share_space.objects.filter(accommodation_id=a, parking=True):
                temp_acc_id.append(a.id)
        accommodations = Accommodation.objects.filter(id__in=temp_acc_id)
    
    ispool = request.GET.get('ispool')
    if ispool:
        temp_acc_id = []
        data['ispool'] = ispool
        for a in accommodations:
            if Share_space.objects.filter(accommodation_id=a, pool=True):
                temp_acc_id.append(a.id)
        accommodations = Accommodation.objects.filter(id__in=temp_acc_id)
    ###############################

    ###############################
    ### give the result within 50 km from destination
    data['city'] = city
    data['adults_quantity'] = adults_quantity
    data['rooms_quantity'] = rooms_quantity
    for accommodation in accommodations:
        lat, lng = formalize_latlng(accommodation.location)
        distance = geodesic((lat, lng), (latitude, longitude)).km
        if distance <= 50.0:
            ret.append({
                'id':accommodation.id,
                'title':accommodation.title,
                'album_address':accommodation.album_address,
                'star_rating':accommodation.star_rating,
                'price':accommodation.price,
                'reviews_num':accommodation.reviews_num,
                'avg_rating':accommodation.avg_rating,
                'lat':lat,
                'lng':lng,
                'distance':distance
            })
    ###############################

    try:
        paginator = Paginator(sorted(ret, key=lambda x : x['distance']), 10)
        listings_on_page = paginator.page(page)
        data["ret"] = listings_on_page.object_list
        data["nb_of_pages"] = paginator.num_pages
        data["has_previous"] = listings_on_page.has_previous()
        data["has_next"] = listings_on_page.has_next()
        data["page_range"] = paginator.page_range
    except EmptyPage:
        data["has_previous"] = False
        data["has_next"] = False
        data["page_range"] = (1,2)
        data["my_listings"] = listings_on_page.object_list
        data["nb_of_pages"] = 1
    data["curr_page"] = page
    data["previous_page"] = page - 1
    data["next_page"] = page + 1

    ###############################
    ### If this is a registered user, 
    ### will show the like records on frontend
    if get_username_by_session(request):
        username = get_username_by_session(request)
        account = Account.objects.get(username=username)
        data['likes'] = UserHistory.objects.filter(owner_id=account).filter(is_favourite=True).values_list('accommodation_id', flat=True)
    ###############################

    data['current_path'] = request.get_full_path()
    return render(request, 'listing.html', data)


##=========================================
# This function is to put or edit a posting
##=========================================
@csrf_exempt
def posting(request):
    # When user want to edit, we load data of this request first
    if request.method == "GET":
        # Get basic data of current user
        data = get_basic_nums_at_profile(request)
        acc_id = request.GET.get('acc_id','')
        if acc_id:
            acc_id = int(acc_id)
            ret = Accommodation.objects.filter(id = acc_id)
            if len(ret) > 0:
                data['acc_id'] = json.dumps(ret[0].id)
                data["acc_title"] = ret[0].title
                data['acc_type'] = ret[0].property_type
                lat, lng = formalize_latlng(ret[0].location)
                if lat and lng:
                    data['long'] = lng
                    data['lat'] = lat
                else:
                    data['long'] = ""
                    data['lat'] = ""

                data['physical_address'] = ret[0].physical_address
                data['album'] = ret[0].album_address
                data['city'] = ret[0].city
                data['description'] = ret[0].description
                data['price'] = str(ret[0].price)
                data['geust_num'] = json.dumps(ret[0].guests_num)
                data['beds_num'] = json.dumps(ret[0].beds_num)
                data['bedrooms_num'] = json.dumps(ret[0].bedrooms_num)
                data['bathrooms_num'] = json.dumps(ret[0].bathrooms_num)
                amenity = Amenity.objects.filter(accommodation_id = acc_id)
                share_space = Share_space.objects.filter(accommodation_id = acc_id)
                if len(amenity) > 0:
                    data['wifi'] = amenity[0].wifi
                    data['air_conditioning'] = amenity[0].air_conditioning
                    data['hair_dryer'] = amenity[0].hair_dryer
                    data['heating'] = amenity[0].heat
                    data['tv'] = amenity[0].tv
                if len(share_space) > 0:
                    data['parking'] = share_space[0].parking
                    data['fitness'] = share_space[0].gym
                    data['pool'] = share_space[0].pool
                albums = AccommodationAlbum.objects.using('db1').get(accommodation_id=acc_id)
                imgs = []
                img_id = 0
                for e in json.loads(albums.urls.replace("'",'"')):
                    imgs.append({'url': e, 'id': img_id})
                    img_id += 1
                data['albums'] = imgs
        return render(request, 'posting.html', data)
    if request.method == "POST":
        check_type = {'true': True, 'false': False, '': False}
        data = {}
        
        title = request.POST.get('title','')
        type_ = request.POST.get('type','')
        long_ = request.POST.get('long','')
        lat = request.POST.get('lat','')
        city = request.POST.get('city','')
        description = request.POST.get('description','')
        price = float(request.POST.get('price','').split(' ')[1])
        bedroom = request.POST.get('bedroom','')
        bed = request.POST.get('bed','')
        geust = request.POST.get('geust','')
        bathroom = request.POST.get('bathroom','')
        
        wifi = check_type[request.POST.get('wifi','')]
        parking = check_type[request.POST.get('parking','')]
        fitness = check_type[request.POST.get('fitness','')]
        pool = check_type[request.POST.get('pool','')]
        heating = check_type[request.POST.get('heating','')]
        air_conditioning = check_type[request.POST.get('air_conditioning','')]
        hair_dryer = check_type[request.POST.get('hair_dryer','')]
        tv = check_type[request.POST.get('tv','')]
        acc_id = request.POST.get('acc_id','')
        imgs = request.POST.get('imgs','')
        imgs = json.loads(imgs)
        address = request.POST.get('address','')
        if acc_id:
            acc_id = int(acc_id)
            acc_album = AccommodationAlbum.objects.using('db1').filter(accommodation_id=acc_id)
            if acc_album.count() == 1:
                acc_album = AccommodationAlbum.objects.using('db1').get(accommodation_id=acc_id)
                acc_album.urls = imgs
                acc_album.save(using='db1')
            elif acc_album.count() == 0:
                acc_album = AccommodationAlbum.objects.using('db1').create(accommodation_id=acc_id, urls=imgs)
                acc_album.save(using='db1')
            Accommodation.objects.filter(id = acc_id).update(
                title = title,
                property_type = type_,
                city = city,
                description = description,
                price = price,
                guests_num = geust,
                bedrooms_num = bedroom,
                beds_num = bed,
                bathrooms_num = bathroom,
                location = '('+str(lat)+','+str(long_)+')',
                album_address = imgs[0],
                picts_num = len(imgs),
                physical_address = address
            )
            Amenity.objects.filter(accommodation_id = acc_id).update(
                tv = tv,
                wifi = wifi,
                heat = heating,
                air_conditioning = air_conditioning,
                hair_dryer = hair_dryer,
            )
            Share_space.objects.filter(accommodation_id = acc_id).update(
                parking = parking,
                pool = pool,
                gym = fitness,
            )
            data['acc_id'] = json.dumps(acc_id)
        else:
            if imgs != []:
                acc_album = AccommodationAlbum.objects.using('db1').create(accommodation_id=acc_id, urls=imgs)
                acc_album.save(using='db1')
            username = get_username_by_session(request)
            owner_id = Account.objects.get(username=username)
            try:
                accommodation = Accommodation(
                    owner_id = owner_id,
                    title = title,
                    description = description,
                    price = price,
                    property_type = type_,
                    city = city,
                    guests_num = geust,
                    bedrooms_num = bedroom,
                    beds_num = bed,
                    bathrooms_num = bathroom,
                    location = '('+str(lat)+','+str(long_)+')',
                    physical_address = address
                )
                accommodation.save()
                acc_id = accommodation.id
                amenity = Amenity(
                    accommodation_id = accommodation,
                    tv = tv,
                    wifi = wifi,
                    heat = heating,
                    air_conditioning = air_conditioning,
                    hair_dryer = hair_dryer,
                )
                share_space = Share_space(
                    accommodation_id = accommodation,
                    parking = parking,
                    pool = pool,
                    gym = fitness,
                )
                amenity.save()
                share_space.save()
            except ValueError:
                data['status'] = 'fail'
                return JsonResponse(data)
            else:
                data['acc_id'] = json.dumps(acc_id)
        data['status'] = 'succeed'
        return JsonResponse(data)

@csrf_exempt
def login(request):
    data = {}
    print('login')
    if request.method == "POST":
        request.session.flush()
        username = request.POST.get('username','')
        password = request.POST.get('password','')
        print('post-ajax: ', username, password)
        varify = Account.objects.filter(username = username).filter(password = password)
        if len(varify) == 0:
            print('fail')
            data['msg'] = 'Wrong Username or Password'
            data['role'] = 'signin'
            data['status'] = 'fail'
        else:
            token = gen_token()
            Account.objects.filter(username = username).update(curr_token = token)
            print('succeed')
            request.session['username'] = username
            request.session['token'] = token
            data = get_basic_nums_at_profile(request)
            data['username'] = username
            data['role'] = 'signin'
            data['status'] = 'succeed'
    print('login data', data)  
    return JsonResponse(data)

@csrf_exempt
def signup(request):
    data = {}
    print('signup')
    if request.method == "POST":
        username = request.POST.get('username','')
        password = request.POST.get('password','')
        password2 = request.POST.get('password2','')
        print('signup: ', username, password, password2)
        varify = Account.objects.filter(username = username)
        if len(varify) == 0 and password == password2:
            print('succeed signup', username, password, password2)
            token = gen_token()
            newAcc = Account.objects.create(
                username = username,
                password = password,
                curr_token = token,
            )
            newAcc.save()
            request.session['username'] = username
            request.session['token'] = token
            data = get_basic_nums_at_profile(request)
            data['username'] = username
            data['role'] = 'signup'
            data['status'] = 'succeed'
        else:
            #messages.add_message(request, messages.INFO, 'signup')
            print('fail signup')
            data['msg'] = 'Invalid Username or Password'
            data['role'] = 'signup'
            data['status'] = 'fail'
    print('singup data', data)
    return JsonResponse(data)

def logout(request):
    request.session.flush()
    return JsonResponse({})

##========================================
# Show details for a single property, include
# basic information and reviews from 
# previous visitor
##========================================
def listing_single(request):
    data = get_basic_nums_at_profile(request)
    if request.method == "GET":
        acc_id = request.GET.get('acc_id','')
        accommodation = Accommodation.objects.get(id=int(acc_id)) # set parameter

        ###############################
        ### Add History
        username = get_username_by_session(request)
        if username:
            save_history(username, accommodation, 'history')
        ###############################
        accommodation_imgs = AccommodationAlbum.objects.get(accommodation_id=int(acc_id)).urls
        order_history = Order.objects.filter(accommodation_id=accommodation)
        occupied_ranges = []
        
        ### only send the dates intervale to frontend that the order have finished
        for order in order_history:
            ### update the order state, if the order not be paid yet
            if order.status == 'not paid yet' and (datetime.datetime.now(tz) - order.order_time).seconds > 1800:
                order.status = 'canceled'
                order.save()
            
            ### only filter out the valid order
            if order.status in ['not paid yet', 'paid', 'finished'] and order.check_out > datetime.date.today():
                order_check_in = str(order.check_in.year)+'-'+str(order.check_in.month)+'-'+str(order.check_in.day)
                order_check_out = str(order.check_out.year)+'-'+str(order.check_out.month)+'-'+str(order.check_out.day-1)
                occupied_ranges.append([order_check_in, order_check_out])
        
        data['guest_or_not'] = False
        if username:
            user = Account.objects.get(username=username)
            guest_or_not = Order.objects.filter(status='paid').filter(accommodation_id=accommodation).filter(username=user)\
                or Order.objects.filter(status='finished').filter(accommodation_id=accommodation).filter(username=user)
            if guest_or_not:
                data['guest_or_not'] = True

        amenity = Amenity.objects.get(accommodation_id=accommodation)
        share_space = Share_space.objects.get(accommodation_id=accommodation)
        urls_str = accommodation_imgs.replace("'",'"')
        accommodation_imgs = json.loads(urls_str)
        imgs_account = len(accommodation_imgs)

        reviews = Review.objects.filter(accommodation_id=accommodation)
        rw_comments = []
        for rw in reviews:
            rw_comments += Comment.objects.filter(review_id=rw.id).select_related('username','reply_to','review_id').order_by('comment_time').reverse()
        reviews_count = len(reviews)
        imgs = []
        img_id = 0
        for rw in reviews:
            try:
                albums = ReviewsAlbum.objects.using('db1').get(review_id=rw.id)
                img_id = 0
                for e in json.loads(albums.urls.replace("'",'"')):
                    imgs.append({'url': e, 'id': img_id, 'review_id':rw.id})
                    img_id += 1
            except Exception:
                continue
        data['rw_albums'] = imgs

        ### split lat and lng from database
        lat, lng = formalize_latlng(accommodation.location)
        ### extract suburb location for weather broadcast
        suburb = trans_latlng_and_address(accommodation.location, 'get_suburb')

        data['username'] = username
        data['accommodation'] = accommodation
        data['img1'] = accommodation_imgs[0]
        data['img2'] = accommodation_imgs[1]
        data['img3'] = accommodation_imgs[2]
        data['rest_imgs'] = accommodation_imgs[3:]
        data['img_num'] = imgs_account - 2
        data['lat'] = lat
        data['lng'] = lng
        data['weather_suburb'] = suburb
        data['amenity'] = amenity
        data['share_space'] = share_space
        data['reviews'] = reviews
        data['reviews_count'] = reviews_count
        data['occupied_ranges'] = json.dumps(occupied_ranges)
        data['rw_comments'] = rw_comments
        data['owner_listing_num'] = Accommodation.objects.filter(owner_id=accommodation.owner_id).count()
        response = render(request, "listing-single.html", data)
        response.delete_cookie('reservation_guests_num')
        response.delete_cookie('reservation_check_in_date')
        response.delete_cookie('reservation_check_out_date')
        response.delete_cookie('reservation_total_days')
        response.delete_cookie('reservation_total_cost')
        response.delete_cookie('reservation_lat')
        response.delete_cookie('reservation_lng')
        response.delete_cookie('reservation_id')
        response.delete_cookie('reservation_deadline')
        return response

##========================================
# To submit or continue to pay a order, the request can be 
##========================================
@csrf_exempt
def reservation(request, accommodation_id):
    username = get_username_by_session(request)
    if not username:
        return HttpResponseRedirect(reverse('index'))
    if request.method == "POST":
        print("======== reservation post ========")
        user = Account.objects.get(username=username)
        accommodation = Accommodation.objects.get(id=accommodation_id)

        ### Check where is the previous page
        check_in_and_out = request.POST.get('bookdates','')
        ### From listing single page, comes to create a new order
        if check_in_and_out:
            total_days = int(request.POST.get('qty5',''))
            guests_num = int(request.POST.get('qty3',''))
            check_list = check_in_and_out.replace(" ","").split("-")
            check_in_date = '-'.join(list(reversed(check_list[0].split("/"))))
            check_out_date = '-'.join(list(reversed(check_list[1].split("/"))))
            check_in_date = datetime.datetime.strptime(check_in_date+" 15:00:00",'%Y-%d-%m %H:%M:%S')
            check_out_date = datetime.datetime.strptime(check_out_date+" 12:00:00",'%Y-%d-%m %H:%M:%S')
            total_cost = accommodation.price*total_days
            latlng = accommodation.location
            lat, lng = formalize_latlng(latlng)
            ### prevent repeate submit booking request
            try:
                order_id = int(request.get_signed_cookie('reservation_id',salt=salt_signiture))
                order = Order.objects.get(id=order_id)
                ### set the deadline for the order, help to count down in frontend
                deadline = order.order_time + datetime.timedelta(hours=10) # UTC+10 timezone
                deadline = deadline + datetime.timedelta(minutes=30) # 30 minutes to pay
                deadline_microsecond = int(str("%06d" % deadline.microsecond)[0:3])
                deadline = time.mktime(deadline.timetuple()) # make the deadline as timestamp to send to frontend
            except:
                order = Order(
                    username = user,
                    accommodation_id = accommodation,
                    check_in = check_in_date,
                    check_out = check_out_date,
                    guests_num = guests_num,
                    total_price = total_cost,
                    status = 'not paid yet'
                )
                order.save()
                ### set the deadline for the order, help to count down in frontend
                deadline = order.order_time + datetime.timedelta(minutes=30) # 30 minutes to pay
                deadline_microsecond = int(str("%06d" % deadline.microsecond)[0:3])
                deadline = time.mktime(deadline.timetuple()) # make the deadline as timestamp to send to frontend

            order_id = order.id
        ### From order history page, continue to pay the order
        else:
            order_id = request.POST.get('order_id', '')
            order = Order.objects.get(id=order_id)
            deadline = order.order_time + datetime.timedelta(hours=10) # UTC+10 timezone
            deadline = deadline + datetime.timedelta(minutes=30) # 30 minutes to pay
            deadline = time.mktime(deadline.timetuple()) # make the deadline as timestamp to send to frontend
            total_days = int(order.total_price/order.accommodation_id.price)
            guests_num = order.guests_num
            check_in_date = datetime.datetime(
                year = order.check_in.year,
                month = order.check_in.month,
                day = order.check_in.day,
                hour = 15
            )
            check_out_date = datetime.datetime(
                year = order.check_out.year,
                month = order.check_out.month,
                day = order.check_out.day,
                hour = 12
            )
            total_cost = order.total_price
            lat, lng = formalize_latlng(order.accommodation_id.location)
        
            ### set the deadline for the order, help to count down in frontend
            deadline = order.order_time + datetime.timedelta(hours=10) # UTC+10 timezone
            deadline = deadline + datetime.timedelta(minutes=30) # 30 minutes to pay
            deadline_microsecond = int(str("%06d" % deadline.microsecond)[0:3])
            deadline = time.mktime(deadline.timetuple()) # make the deadline as timestamp to send to frontend

        content = {
            'user':user,
            'accommodation':accommodation,
            'guests_num':guests_num,
            'check_in_date':check_in_date,
            'check_out_date':check_out_date,
            'total_days':total_days,
            'total_cost':total_cost,
            'lat':lat,
            'lng':lng,
            'order_id':order_id,
            'deadline':deadline * 1000 + deadline_microsecond # timestamp
        }
        ### store data in cookie
        response = render(request, "reservation.html", content)
        response.set_signed_cookie('reservation_check_in_date', check_in_date, salt=salt_signiture)
        response.set_signed_cookie('reservation_check_out_date', check_out_date, salt=salt_signiture)
        response.set_signed_cookie('reservation_total_days', total_days, salt=salt_signiture)
        response.set_signed_cookie('reservation_guests_num', guests_num, salt=salt_signiture)
        response.set_signed_cookie('reservation_total_cost', total_cost, salt=salt_signiture)
        response.set_signed_cookie('reservation_lat', lat, salt=salt_signiture)
        response.set_signed_cookie('reservation_lng', lng, salt=salt_signiture)
        response.set_signed_cookie('reservation_id', order_id, salt=salt_signiture)
        response.set_signed_cookie('reservation_deadline', deadline * 1000 + deadline_microsecond, salt=salt_signiture)
        return response
    else:
        print("======== reservation get ========")
        return HttpResponseRedirect(reverse('index'))

##====================================================================================
# To pay money for the order, this is a POST function, if not the page will goto index
##====================================================================================
@csrf_exempt
def confirm_reservation(request, accommodation_id):
    if request.method == "POST":
        print("======== confirm reservation post ========")
        username = get_username_by_session(request)
        user = Account.objects.get(username=username)
        accommodation = Accommodation.objects.get(id=accommodation_id)
        ### get data from cookie
        check_in_date = datetime.datetime.strptime(request.get_signed_cookie('reservation_check_in_date',salt=salt_signiture), '%Y-%m-%d %H:%M:%S')
        total_days = int(request.get_signed_cookie('reservation_total_days',salt=salt_signiture))
        check_out_date = datetime.datetime.strptime(request.get_signed_cookie('reservation_check_out_date',salt=salt_signiture), '%Y-%m-%d %H:%M:%S')
        guests_num = int(request.get_signed_cookie('reservation_guests_num',salt=salt_signiture))
        total_cost = float(request.get_signed_cookie('reservation_total_cost',salt=salt_signiture))
        payment_card = request.POST.get('payment_card','')
        expiry_month = int(request.POST.get('expiry_month',''))
        expiry_year = int(request.POST.get('expiry_year',''))
        cvv = int(request.POST.get('cvv',''))
        order = Order.objects.get(id=int(request.get_signed_cookie('reservation_id',salt=salt_signiture)))
        if order.status != 'not paid yet':
            return HttpResponseRedirect(reverse('booking_history'))
        ### in case some error may happend
        try:
            order.card_number = payment_card
            order.expiry_month = expiry_month
            order.expiry_year = expiry_year
            order.cvv = cvv
            order.order_time = datetime.datetime.now()
            order.status = 'paid'

            order.save()
            response = JsonResponse({'status':'succeed'})
            response.delete_cookie('reservation_guests_num')
            response.delete_cookie('reservation_check_in_date')
            response.delete_cookie('reservation_check_out_date')
            response.delete_cookie('reservation_total_days')
            response.delete_cookie('reservation_total_cost')
            response.delete_cookie('reservation_lat')
            response.delete_cookie('reservation_lng')
            response.delete_cookie('reservation_id')
            response.delete_cookie('reservation_deadline')
            return response
        except Exception:
            print(Exception)
            return JsonResponse({'status':'failed'})
    else:
        print("======== confirm reservation get ========")
        return HttpResponseRedirect(reverse('index'))

##=====================================================================================
# edit_profile is for users to update their information like name, email, descriptions;
# While GET method presents user information on webpage, 
# POST method updates user information in SQLite DB according to what they submited
##=====================================================================================
@csrf_exempt
def edit_profile(request):
    data = get_basic_nums_at_profile(request)
    print('user profile')
    if request.method == "POST":
        print('Post')
        username = get_username_by_session(request)
        # Retrieve information from frontend
        name = request.POST.get('name','')
        email = request.POST.get('email','')
        website = request.POST.get('website','')
        about = request.POST.get('about','')
        print('post-ajax: ', name, email, website, about)
        # Store in Account
        user = Account.objects.get(username=username)
        user.name = name
        user.email = email
        user.url = website
        user.description = about
        user.save()
        # Show updated information on webpage
        portrait_address = user.portrait_address
        data["pro_name"] = name
        data["pro_email"] = email
        data["pro_website"] = website
        data["pro_about"] = about
        data["show_img"] = portrait_address
        print('succeed')
        return JsonResponse(data)
    else:
        print('Get')
        # Check whether user login or not
        username = get_username_by_session(request)
        # if login -> show profile page
        if username:
            user = Account.objects.get(username=username)
            name = user.name
            email = user.email
            website = user.url
            about = user.description
            data = get_basic_nums_at_profile(request)
            print('username: ', username)
            data["pro_name"] = name
            data["pro_email"] = email
            data["pro_website"] = website
            data["pro_about"] = about
            print("data: ", data)
            return render(request, 'dashboard-myprofile.html', data)
        # othervise, show homepage
        else:
            return HttpResponseRedirect(reverse('index'))

##=====================================================================================
# upload_user_protrait is on the same page of edit_profile page; it allows users to
# upload their portrait and store the corresponding image on Google Cloud Platform and
# the image address into SQLiteDB.
##=====================================================================================
@csrf_exempt
def upload_user_protrait(request):
    print("upload_user_protrait")
    username = get_username_by_session(request)
    data = get_basic_nums_at_profile(request)
    if request.method == "POST":
        # get image content from frontend
        img_content = request.POST.get('img', '').split(',')[1]
        print(type(img_content), len(img_content))
        print(img_content)
        # decode image content
        img = base64.b64decode(img_content)
        # generate a unique filename and upload image onto google cloud
        file_name = generate_filename("user", ".jpg")
        file = default_storage.open(file_name, 'w')
        file.write(img)
        file.close()
        # return address of portrait to frontend
        data['show_img'] = 'https://storage.cloud.google.com/accomodation9900_property_images/'+file_name
        # save it to Account protrait
        if username:
            Account.objects.filter(username=username).update(portrait_address=data['show_img'])
        return JsonResponse(data)
    else:
        if username:
            user = Account.objects.get(username=username)
            name = user.name
            email = user.email
            website = user.url
            about = user.description
            print('username: ', username)
            data["pro_name"] = name
            data["pro_email"] = email
            data["pro_website"] = website
            data["pro_about"] = about
            data["show_img"] = user.portrait_address
            print("data: ", data)
        return render(request, 'dashboard-myprofile.html', data)

##=====================================================================================
# user_listings, user_active_listings, user_pending_listings are functions to help 
# users maintain their properties. This is to present properties owned by users with 
# options to filter out some of them according to status of properties 
# i.e. active or pending
##=====================================================================================
@csrf_exempt
def user_listings(request):
    print("user_listings")
    data = get_basic_nums_at_profile(request)
    page = request.GET.get('page')
    if not page:
        page = 1
    else:
        page = int(page)
    username = get_username_by_session(request)
    if request.method == "GET":
        if username:
            user = Account.objects.get(username=username)
            my_listings = Accommodation.objects.filter(owner_id=user)
            # add paginator
            try:
                paginator = Paginator(my_listings, 10)
                listings_on_page = paginator.page(page)
                data["my_listings"] = listings_on_page.object_list
                data["nb_of_pages"] = paginator.num_pages
                data["has_previous"] = listings_on_page.has_previous()
                data["has_next"] = listings_on_page.has_next()
                data["page_range"] = paginator.page_range
            except EmptyPage:
                data["has_previous"] = False
                data["has_next"] = False
                data["page_range"] = (1,2)
                data["my_listings"] = listings_on_page.object_list
                data["nb_of_pages"] = 1
            data["listing_type"] = "ALL"
            data["curr_page"] = page
            data["previous_page"] = page - 1
            data["next_page"] = page + 1
        return render(request, "dashboard-listing-table.html", data)
@csrf_exempt
def user_active_listings(request):
    print("user_active_listings")
    data = get_basic_nums_at_profile(request)
    page = request.GET.get('page')
    if not page:
        page = 1
    else:
        page = int(page)
    username = get_username_by_session(request)
    if request.method == "GET":
        if username:
            user = Account.objects.get(username=username)
            my_listings = Accommodation.objects.filter(owner_id=user).filter(is_public=True)
            #data["my_listings"] = my_listings
            # add paginator
            try:
                paginator = Paginator(my_listings, 10)
                listings_on_page = paginator.page(page)
                data["my_listings"] = listings_on_page.object_list
                data["nb_of_pages"] = paginator.num_pages
                data["has_previous"] = listings_on_page.has_previous()
                data["has_next"] = listings_on_page.has_next()
                data["page_range"] = paginator.page_range
            except EmptyPage:
                data["has_previous"] = False
                data["has_next"] = False
                data["page_range"] = (1,2)
                data["my_listings"] = listings_on_page.object_list
                data["nb_of_pages"] = 1
            data["listing_type"] = "Active"
            data["curr_page"] = page
            data["previous_page"] = page - 1
            data["next_page"] = page + 1
        return render(request, "dashboard-listing-table.html", data)
@csrf_exempt
def user_pending_listings(request):
    print("user_pending_listings")
    data = get_basic_nums_at_profile(request)
    page = request.GET.get('page')
    if not page:
        page = 1
    else:
        page = int(page)
    username = get_username_by_session(request)
    if request.method == "GET":
        if username:
            data = get_basic_nums_at_profile(request)
            user = Account.objects.get(username=username)
            my_listings = Accommodation.objects.filter(owner_id=user).filter(is_public=False)
            # add paginator
            try:
                paginator = Paginator(my_listings, 10)
                listings_on_page = paginator.page(page)
                data["my_listings"] = listings_on_page.object_list
                data["nb_of_pages"] = paginator.num_pages
                data["has_previous"] = listings_on_page.has_previous()
                data["has_next"] = listings_on_page.has_next()
                data["page_range"] = paginator.page_range
            except EmptyPage:
                data["has_previous"] = False
                data["has_next"] = False
                data["page_range"] = (1,2)
                data["my_listings"] = listings_on_page.object_list
                data["nb_of_pages"] = 1
            data["listing_type"] = "Pending"
            data["curr_page"] = page
            data["previous_page"] = page - 1
            data["next_page"] = page + 1
    return render(request, "dashboard-listing-table.html", data)

##=====================================================================================
# archiveListing, publicListing are functions for users to public an existed property 
# or to archive a property
##=====================================================================================
@csrf_exempt
def archiveListing(request):
    print("archiveListing")
    if request.method == "GET":
        acc_id = request.GET.get('acc_id','')
        if acc_id:
            Accommodation.objects.filter(id = int(acc_id)).update(is_public=False)
        curr_url = request.path
        print("curr_url: ", curr_url)
        parent_url = curr_url.rsplit('/',2)[0]
        print(parent_url)
        if parent_url == "/user_listings_active":
            return HttpResponseRedirect(reverse('user_active_listings'))
        elif parent_url == "/user_listings_pending":
            return HttpResponseRedirect(reverse('user_pending_listings'))
        return HttpResponseRedirect(reverse('user_listings'))
@csrf_exempt
def publicListing(request):
    print("publicListing")
    if request.method == "GET":
        acc_id = request.GET.get('acc_id','')
        if acc_id:
            accommodation = Accommodation.objects.filter(id = int(acc_id))
            accommodation.update(is_public=True)
            """ if accommodation.physical_address and accommodation.title and accommodation.guests_num and accommodation.bedrooms_num and accommodation.beds_num and accommodation.bathrooms_num and accommodation.location and accommodation.album_address\
            and accommodation.picts_num >= 4 and accommodation.price:
                accommodation.update(is_public=True) """
        curr_url = request.path
        print("curr_url: ", curr_url)
        parent_url = curr_url.rsplit('/',2)[0]
        print(parent_url)
        if parent_url == "/user_listings_active":
            return HttpResponseRedirect(reverse('user_active_listings'))
        elif parent_url == "/user_listings_pending":
            return HttpResponseRedirect(reverse('user_pending_listings'))
        return HttpResponseRedirect(reverse('user_listings'))

##=====================================================================================
# This function is also embedded in edit_profile page; it allows users to change
# their password given that they provide a correct old password. 
##=====================================================================================
@csrf_exempt
def changePwd(request):
    print("changePwd")
    data ={}
    username = get_username_by_session(request)
    if username:
        data = get_basic_nums_at_profile(request)
    if request.method == "GET":
        return render(request, "dashboard-password.html", data)
    else:
        curPwd = request.POST.get('curPwd','')
        newPwd = request.POST.get('newPwd','')
        confPwd = request.POST.get('confPwd','')
        verify = Account.objects.filter(username = username, password = curPwd)
        if len(verify) != 0 and newPwd == confPwd:
            print('succeed changePwd', username, newPwd, confPwd)
            Account.objects.filter(username = username).update(password = confPwd)
            data['username'] = username
            data['role'] = 'changePwd'
            data['status'] = 'succeed'
        else:
            data['msg'] = 'Invalid Password'
            data['role'] = 'changePwd'
            data['status'] = 'fail'
        return JsonResponse(data)

##=====================================================================================
# reviews_for_host is to present all reviews from guests of properties owned by users
##=====================================================================================
@csrf_exempt
def reviews_for_host(request):
    print("reviews_for_host")
    data = {}
    username = get_username_by_session(request)
    if request.method == "GET":
        page = request.GET.get('page')
        if not page:
            page = 1
        else:
            page = int(page)
        if username:
            data = get_basic_nums_at_profile(request)
            user = Account.objects.get(username=username)
            my_reviews = Review.objects.filter(acc_owner_id=user).select_related('accommodation_id','reviewer_id').order_by('date').reverse()
            print(my_reviews.count())
            print(type(my_reviews))
            # add paginator
            try:
                paginator = Paginator(my_reviews, 10)
                reviews_on_page = paginator.page(page)
                data["my_reviews"] = reviews_on_page.object_list
                data["nb_of_pages"] = paginator.num_pages
                data["has_previous"] = reviews_on_page.has_previous()
                data["has_next"] = reviews_on_page.has_next()
                data["page_range"] = paginator.page_range
            except EmptyPage:
                data["has_previous"] = False
                data["has_next"] = False
                data["page_range"] = (1,2)
                data["my_reviews"] = reviews_on_page.object_list
                data["nb_of_pages"] = 1
            data["reviews_type"] = "HOST"
            data["curr_page"] = page
            data["previous_page"] = page - 1
            data["next_page"] = page + 1
            rw_comments = []
            for rw in reviews_on_page.object_list:
                rw_comments += Comment.objects.filter(review_id=rw.id).select_related('username','reply_to','review_id').order_by('comment_time').reverse()
            imgs = []
            img_id = 0
            for rw in reviews_on_page.object_list:
                try:
                    albums = ReviewsAlbum.objects.using('db1').get(review_id=rw.id)
                    img_id = 0
                    for e in json.loads(albums.urls.replace("'",'"')):
                        imgs.append({'url': e, 'id': img_id, 'review_id':rw.id})
                        img_id += 1
                except Exception:
                    continue
            data['rw_albums'] = imgs
            print(len(reviews_on_page))
            print("reviews_on_page: ", reviews_on_page.object_list)
            print("rw_comments: ", rw_comments)
            data["rw_comments"] = rw_comments
        return render(request, "dashboard-review.html", data)

##=====================================================================================
# user_reviews is to present all reviews made by users as a guest
##=====================================================================================
@csrf_exempt
def user_reviews(request):
    print("user_reviews")
    data = {}
    username = get_username_by_session(request)
    if request.method == "GET":
        page = request.GET.get('page')
        if not page:
            page = 1
        else:
            page = int(page)
        if username:
            data = get_basic_nums_at_profile(request)
            user = Account.objects.get(username=username)
            my_reviews = Review.objects.filter(reviewer_id=user).select_related('accommodation_id','acc_owner_id').order_by('date').reverse()
            print(my_reviews.count())
            print(type(my_reviews))
            # add paginator
            try:
                paginator = Paginator(my_reviews, 10)
                reviews_on_page = paginator.page(page)
                data["my_reviews"] = reviews_on_page.object_list
                data["nb_of_pages"] = paginator.num_pages
                data["has_previous"] = reviews_on_page.has_previous()
                data["has_next"] = reviews_on_page.has_next()
                data["page_range"] = paginator.page_range
            except EmptyPage:
                data["has_previous"] = False
                data["has_next"] = False
                data["page_range"] = (1,2)
                data["my_reviews"] = reviews_on_page.object_list
                data["nb_of_pages"] = 1
            data["reviews_type"] = "GUEST"
            data["curr_page"] = page
            data["previous_page"] = page - 1
            data["next_page"] = page + 1
            rw_comments = []
            for rw in reviews_on_page.object_list:
                rw_comments += Comment.objects.filter(review_id=rw.id).select_related('username','reply_to','review_id').order_by('comment_time').reverse()
            imgs = []
            img_id = 0
            for rw in reviews_on_page.object_list:
                try:
                    albums = ReviewsAlbum.objects.using('db1').get(review_id=rw.id)
                    img_id = 0
                    for e in json.loads(albums.urls.replace("'",'"')):
                        imgs.append({'url': e, 'id': img_id, 'review_id':rw.id})
                        img_id += 1
                except Exception:
                    continue
            data['rw_albums'] = imgs
            print(len(reviews_on_page))
            print(reviews_on_page)
            print("rw_comments: ", rw_comments)
            data["rw_comments"] = rw_comments
        return render(request, "dashboard-review.html", data)

##=====================================================================================
# reply_to_review and reply_to_reply are used in both property page(listing_single.html)
# and user review module (dashboard-review.html);
# reply_to_review is for users to reply to a review and store the content of comments 
# in comment table.
# reply_to_reply is for users to reply to a comment and store the content of comments
# in comment table.
# After operation, webpage would not be fully refreshed but will partially refreshed
# using Ajax in the frontend.
##=====================================================================================
@csrf_exempt
def reply_to_review(request):
    print("reply_to_review")
    data = {}
    username = get_username_by_session(request)
    data = get_basic_nums_at_profile(request)
    if request.method == "POST":
        if username:
            review_id = request.POST.get('review_id')
            reply = request.POST.get('textarea_value')
            print(review_id, reply)
            review = Review.objects.get(id=int(review_id))
            owner_id = review.acc_owner_id
            acc_id = review.accommodation_id
            reply_to = review.reviewer_id
            comment_user = Account.objects.get(username=username)
            rw = Comment.objects.create(review_id=review, acc_owner_id=owner_id, accommodation_id=acc_id, reply_to=reply_to, username=comment_user, content=reply)
            rw.save()
            data["new_rw_id"] = json.dumps(rw.id)
            data["new_rw_rp_id"] = rw.reply_to.username
            data["new_rw_rp_name"] = rw.reply_to.name
            data["new_rw_user"] = comment_user.name
            data["new_cm_time"] = rw.comment_time
            data["rq_review_id"] = json.dumps(rw.review_id.id)
            print(rw)
            data['status'] = '200'
            return JsonResponse(data)
        data['status'] = '403'
        return JsonResponse(data)
@csrf_exempt
def reply_to_reply(request):
    print("reply_to_reply")
    data = {}
    username = get_username_by_session(request)
    data = get_basic_nums_at_profile(request)
    if request.method == "POST":
        if username:
            comment_id = request.POST.get('comment_id')
            reply = request.POST.get('textarea_value')
            print(comment_id, reply)
            comm = Comment.objects.get(id=int(comment_id))
            review = comm.review_id
            owner_id = comm.acc_owner_id
            acc_id = comm.accommodation_id
            reply_to = comm.username
            comment_user = Account.objects.get(username=username)
            cm = Comment.objects.create(review_id=review, acc_owner_id=owner_id, accommodation_id=acc_id, reply_to=reply_to, username=comment_user, content=reply)
            cm.save()
            data["new_rw_id"] = json.dumps(cm.id)
            data["new_rw_rp_id"] = cm.reply_to.username
            data["new_rw_rp_name"] = cm.reply_to.name
            data["new_rw_user"] = comment_user.name
            data["new_cm_time"] = cm.comment_time
            data["rq_review_id"] = json.dumps(cm.review_id.id)
            print(cm)
            data['status'] = '200'
            return JsonResponse(data)
        data['status'] = '403'
        return JsonResponse(data)

##=====================================================================================
# upload_review_photo is triggered when users upload an image in adding review module;
# this function will store image to Google cloud and return corresponding image address
# to frontend
##=====================================================================================
@csrf_exempt
def upload_review_photo(request):
    print('upload_review_photo')
    if request.method == "POST":
        data = get_basic_nums_at_profile(request)
        username = get_username_by_session(request)
        owner_id = Account.objects.get(username=username)
        acc_id = request.POST.get('acc_id','')
        review_id = request.POST.get('review_id','')
        img_content = request.POST.get('img', '').split(',')[1]
        print(type(img_content), len(img_content))
        # decode image
        img = base64.b64decode(img_content)
        # genrate unique filename
        file_name = generate_filename("review", '.jpg')
        # store image on google cloud
        file = default_storage.open(file_name, 'w')
        file.write(img)
        file.close()
        # return an image address
        data['img_url'] = 'https://storage.cloud.google.com/accomodation9900_property_images/'+file_name
        print('url: ', data['img_url'])
        return JsonResponse(data)

##=====================================================================================
# delete_review_photo is triggered when users delete an image in adding review module;
# this function will delete image from Google cloud according to image address;
##=====================================================================================
@csrf_exempt
def delete_review_photo(request):
    if request.method == "POST":
        data = get_basic_nums_at_profile(request)
        username = get_username_by_session(request)
        owner_id = Account.objects.get(username=username)
        img_raw = request.POST.get('img')
        # retrive image filename
        img = img_raw.replace("https://storage.cloud.google.com/accomodation9900_property_images/","")
        storage_client = storage.Client.from_service_account_json("backend/Accommodation9900Storage-449e7001109e.json")
        bucket = storage_client.get_bucket('accomodation9900_property_images')
        # delete image file according to image filename
        blob = bucket.blob(img)
        blob.delete()
        return JsonResponse(data) 

##=====================================================================================
# add_reviews is only available for users who have an order on this property with 
# order status as "complete" or "paid".
# When a POST method is requsted, this function will retrive score and review content 
# and store them in SQLiteDB; and also retrieve Google Cloud address of images and 
# store them on MingoDB
# after that, webpage will be refreshed.
##=====================================================================================
@csrf_exempt
def add_reviews(request, acc_id):
    print("add_reviews")
    username = get_username_by_session(request)
    data = get_basic_nums_at_profile(request)
    if request.method == "POST":
        if username:
            my_score = float(request.POST.get('my_score'))
            my_review = request.POST.get('my_review')
            imgs = request.POST.get('imgs_url','')
            imgs = json.loads(imgs)
            print(imgs)
            print(my_score, my_review)
            user = Account.objects.get(username=username)
            name = user.name
            acc = Accommodation.objects.get(id=acc_id)
            owner = acc.owner_id
            # create a new review
            review = Review.objects.create(accommodation_id=acc, acc_owner_id=owner, reviewer_id=user, reviewer_name=name, score=float(my_score), comments=my_review)
            review.save()
            # update average score and number of reviews in accommodation table
            acc.reviews_num += 1
            acc.avg_rating = (acc.avg_rating + my_score) / acc.reviews_num
            acc.save()
            # save image address to mongoDB
            rw_album = ReviewsAlbum.objects.using('db1').filter(review_id=review.id)
            if rw_album.count() == 1:
                rw_album = ReviewsAlbum.objects.using('db1').get(review_id=review.id)
                rw_album.urls = imgs
                rw_album.save(using='db1')
            elif rw_album.count() == 0:
                rw_album = ReviewsAlbum.objects.using('db1').create(review_id=review.id, urls=imgs)
                rw_album.save(using='db1')
            data['status'] = '200'
            return JsonResponse(data)
        data['status'] = '403'
        return JsonResponse(data)

##=====================================================================================
# add_feedbacks is for users to give a feedback on request pages.
# When a POST method is requsted, this function will store content of feedback in 
# requestreview table in SQLiteDB.
##=====================================================================================
@csrf_exempt
def add_feedbacks(request, request_id):
    print("add_feedbacks")
    username = get_username_by_session(request)
    data = get_basic_nums_at_profile(request)
    if request.method == "POST":
        if username:
            my_feedback = request.POST.get('my_feedback')
            print(my_feedback)
            user = Account.objects.get(username=username)
            name = user.name
            rq = Request.objects.get(id=request_id)
            owner = rq.owner_id
            # add a new feedback
            rq_rw = RequestReview.objects.create(request_id=rq, request_owner_id=owner, reply_id=user, reply_name=name, comments=my_feedback)
            rq_rw.save()
            data['status'] = '200'
            return JsonResponse(data)
        data['status'] = '403'
        return JsonResponse(data)

##=====================================================================================
# The following two functions are similar to reply_to_review and reply_to_reply 
# except that they are using requestcomment table in SQLiteDB to store the comments 
# under feedbacks.
##=====================================================================================
@csrf_exempt
def reply_to_feedbacks(request):
    print("reply_to_feedbacks")
    username = get_username_by_session(request)
    data = get_basic_nums_at_profile(request)
    if request.method == "POST":
        if username:
            feedback_id = request.POST.get('feedback_id')
            reply = request.POST.get('textarea_value')
            print(feedback_id, reply)
            review = RequestReview.objects.get(id=int(feedback_id))
            owner_id = review.request_owner_id
            rq_id = review.request_id
            reply_to = review.reply_id
            user = Account.objects.get(username=username)
            rw = RequestComment(rq_review_id=review, request_owner_id=owner_id, request_id=rq_id, reply_to=reply_to, username=user, content=reply)
            rw.save()
            data["new_rw_id"] = json.dumps(rw.id)
            data["new_rw_rp_id"] = rw.reply_to.username
            data["new_rw_rp_name"] = rw.reply_to.name
            data["new_rw_user"] = user.name
            data["new_cm_time"] = rw.comment_time
            data["rq_review_id"] = json.dumps(rw.rq_review_id.id)
            print(rw)
            data['status'] = '200'
            return JsonResponse(data)
        data['status'] = '403'
        return JsonResponse(data)
@csrf_exempt
def reply_reply_request(request):
    print("reply_reply_request")
    data = {}
    username = get_username_by_session(request)
    data = get_basic_nums_at_profile(request)
    if request.method == "POST":
        if username:
            comment_id = request.POST.get('comment_id')
            reply = request.POST.get('textarea_value')
            print(comment_id, reply)
            comm = RequestComment.objects.get(id=int(comment_id))
            review = comm.rq_review_id
            owner_id = comm.request_owner_id
            rq_id = comm.request_id
            reply_to = comm.username
            comment_user = Account.objects.get(username=username)
            cm = RequestComment.objects.create(rq_review_id=review, request_owner_id=owner_id, request_id=rq_id, reply_to=reply_to, username=comment_user, content=reply)
            cm.save()
            data["new_rw_id"] = json.dumps(cm.id)
            data["new_rw_rp_id"] = cm.reply_to.username
            data["new_rw_rp_name"] = cm.reply_to.name
            data["new_rw_user"] = comment_user.name
            data["new_cm_time"] = cm.comment_time
            data["rq_review_id"] = json.dumps(cm.rq_review_id.id)
            print(cm)
            data['status'] = '200'
            return JsonResponse(data)
        data['status'] = '403'
        return JsonResponse(data)

##========================================
# Check the previous order
##========================================
@csrf_exempt
def booking_history(request):
    username = get_username_by_session(request)
    ### if cannot get username, return to index page and alert that user should login
    ### before view booking history
    if username == None:
        return HttpResponseRedirect(reverse(index))
    username = Account.objects.get(username=username)
    data = get_basic_nums_at_profile(request)
    if request.method == "GET":
        print('======== booking history get ========')
        page = request.GET.get('page')

        ### Get the flag from url link which indicate which type of order shoule be listed
        host_or_visitor = request.GET.get('host_or_visitor')

        if not page:
            page = 1
        else:
            page = int(page)
        orders = []

        ### filter out the orders for user
        if not host_or_visitor or host_or_visitor == "visitor":
            for order in Order.objects.filter(username=username):
                deadline = order.order_time + datetime.timedelta(hours=10) # UTC+10 timezone
                deadline = deadline + datetime.timedelta(minutes=30) # 30 minutes to pay
                deadline_microsecond = int(str("%06d" % deadline.microsecond)[0:3])
                deadline = time.mktime(deadline.timetuple()) # make the deadline as timestamp to send to frontend
                orderinfo = {}
                orderinfo['tag'] = "host"
                orderinfo['order_time'] = order.order_time # datetime
                orderinfo['order_time_year'] = order.order_time.year
                orderinfo['order_time_month'] = order.order_time.month
                orderinfo['order_time_day'] = order.order_time.day
                orderinfo['order_time_hour'] = order.order_time.hour
                orderinfo['order_time_minute'] = order.order_time.minute
                orderinfo['order_time_second'] = order.order_time.second
                orderinfo['name'] = order.accommodation_id.owner_id.name
                orderinfo['email'] = order.accommodation_id.owner_id.email
                orderinfo['acc_title'] = order.accommodation_id.title
                orderinfo['acc_id'] = order.accommodation_id.id
                orderinfo['check_in']=order.check_in
                orderinfo['check_out'] = order.check_out
                orderinfo['guests_num'] = order.guests_num
                orderinfo['card_num'] = hide_card_number(order.card_number)
                orderinfo['total_price'] = order.total_price
                orderinfo['deadline'] = deadline * 1000 + deadline_microsecond # timestamp
                if order.check_out <= datetime.date.today() and order.status == 'paid':
                    order.status = 'finished'
                    order.save()
                if (datetime.datetime.now(tz) - order.order_time.replace()).seconds > 1800 and order.status == 'not paid yet':
                    order.status = 'canceled'
                    order.save()
                orderinfo['status'] = order.status
                orderinfo['order_id'] = order.id
                orderinfo['acc_price'] = order.accommodation_id.price
                orders.append(orderinfo)

        ### filter out the orders for host
        if not host_or_visitor or host_or_visitor == "host":
            accommodations = Accommodation.objects.filter(owner_id=username)
            for accommodation in accommodations:
                for order in Order.objects.filter(accommodation_id=accommodation):
                    orderinfo = {}
                    orderinfo['tag'] = "visitor"
                    orderinfo['order_time'] = order.order_time
                    orderinfo['order_time_year'] = order.order_time.year
                    orderinfo['order_time_month'] = order.order_time.month
                    orderinfo['order_time_day'] = order.order_time.day
                    orderinfo['order_time_hour'] = order.order_time.hour
                    orderinfo['order_time_minute'] = order.order_time.minute
                    orderinfo['order_time_second'] = order.order_time.second
                    orderinfo['name'] = order.username.name
                    orderinfo['email'] = order.username.email
                    orderinfo['acc_title'] = order.accommodation_id.title
                    orderinfo['acc_id'] = order.accommodation_id.id
                    orderinfo['check_in']=order.check_in
                    orderinfo['check_out'] = order.check_out
                    orderinfo['guests_num'] = order.guests_num
                    orderinfo['total_price'] = order.total_price
                    if order.check_out >= datetime.date.today() and order.status == 'paid':
                        order.status = 'finished'
                        order.save()
                    if (datetime.datetime.now(tz) - order.order_time.replace()).seconds > 1800 and order.status == 'not paid yet':
                        order.status = 'canceled'
                        order.save()
                    orderinfo['status'] = order.status
                    orders.append(orderinfo)
        
        try:
            paginator = Paginator(list(sorted(orders, key=lambda x : x['order_time'], reverse=True)), 10)
            order_lisitng = paginator.page(page)
            data["orders"] = order_lisitng.object_list
            data["nb_of_pages"] = paginator.num_pages
            data["has_previous"] = order_lisitng.has_previous()
            data["has_next"] = order_lisitng.has_next()
            data["page_range"] = paginator.page_range
        except EmptyPage:
            data["has_previous"] = False
            data["has_next"] = False
            data["page_range"] = (1,2)
            data["orders"] = order_lisitng.object_list
            data["nb_of_pages"] = 1
        data["curr_page"] = page
        data["previous_page"] = page - 1
        data["next_page"] = page + 1
        return render(request, "dashboard-bookings.html", data)

##==========================================
# When order not be paid, it can be canceled
##==========================================
@csrf_exempt
def cancel_order(request):
    order_id = request.POST.get('order_id','')
    try:
        print(order_id)
        order = Order.objects.get(id=order_id)
        order.status = "canceled"
        order.save()
        return JsonResponse({'status':'succeed'})
    except:
        return JsonResponse({'status':'fail'})

##===================================================
# Before order have been finishen, order canbe refund
##===================================================
@csrf_exempt
def refund_order(request):
    order_id = request.POST.get('order_id','')
    try:
        print(order_id)
        order = Order.objects.get(id=order_id)
        order.status = "refunded"
        order.save()
        return JsonResponse({'status':'succeed'})
    except:
        return JsonResponse({'status':'fail'})


##========================================
# This function is used to update database
##========================================
def updata_data(request):
    print("[INFO] Updating database")
    set_guests_bedrooms_num()
    return HttpResponse('OK!')

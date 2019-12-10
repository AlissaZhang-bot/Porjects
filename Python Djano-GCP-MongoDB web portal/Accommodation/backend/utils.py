##===================================================
# Some useful functions in our backend
##===================================================
import secrets
import json
from .models import Account, Accommodation, Review, Order, Request, UserHistory
from django.core.files.storage import default_storage
import re
import certifi
import ssl
import geopy.geocoders
from geopy.geocoders import Nominatim
import datetime
import django
import json
import pandas as pd
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
import heapq

##=======================================
# Recommendation model begin
# This function is to load metadata for 
# all accommmodations and user profile data
##=======================================
def load(request):
    username = get_username_by_session(request)
    history = []
    favorite = []
    if username:
        account = Account.objects.get(username=username)
        # Construct user profile data by using searching history and favorite
        history = UserHistory.objects.filter(owner_id=account).filter(is_history=True).values_list('accommodation_id', flat=True)
        favorite = UserHistory.objects.filter(owner_id=account).filter(is_favourite=True).values_list('accommodation_id', flat=True)
        print('len: ', history, favorite)
    data = Accommodation.objects.all()
    transfer = {'False': 0, 'True': 1}
    L = []
    _L = []
    for e in data:
        L += [[]]
        L[-1].append(e.title)
        L[-1].append(e.price)
        L[-1].append(e.bathrooms_num)
        L[-1].append(e.bedrooms_num)
        L[-1].append(e.beds_num)
        L[-1].append(e.guests_num)
        L[-1].append(int(transfer[str(e.is_new_listing)]))
        L[-1].append(e.reviews_num)
        L[-1].append(e.star_rating)
        L[-1].append(e.avg_rating)
        L[-1].append(int(transfer[str(e.can_instant_book)]))
        if e.id in history or e.id in favorite:
            print(e, L[-1])
            _L.append(L[-1])
    print('_L', _L)

    # If there is no history record, 
    # we use top 10 value of accmmodations 
    # sorting by average star rating
    if _L == []:
        _L = pd.DataFrame(L)
        _L.sort_values(9, inplace=True)
        return pd.DataFrame(L), _L.tail()
    
    return pd.DataFrame(L), pd.DataFrame(_L)

##=======================================
# This function is to construct matrices for 
# all accommmodations and user profile data
##=======================================
def cb_loadData(request):
    df, user_profile_matrix = load(request)
    # Prepare the Data Series for All the Accommendation
    df = df.reset_index()
    titles = df[0]
    acc_list = pd.Series(df.index, index=titles)
    # Choose the first 10 columns as features
    df = df[[1,2,3,4,5,6,7,8,9,10]]
    user_profile_matrix = user_profile_matrix[[1,2,3,4,5,6,7,8,9,10]]
    # Construct the user profile vector by using mean value of each feature
    user_profile_vector = pd.DataFrame(user_profile_matrix.describe().iloc[1]).T
    
    return df, user_profile_vector, acc_list

##=====================================================
# This function is to compute similarities
# between all accommmodations and user profile vector
##=====================================================
def cosSimilarity(matrix, user_profile_vector):
    similarity_matrix = cosine_similarity(matrix, user_profile_vector)
    return similarity_matrix

##=======================================
# This function is to make recommends results
# based on the sorted similarities
##=======================================
def recForOneItem(acc_list_df, similarity_matrix, num_rec):
    # Get the Similarity Score
    similarity_score = list(enumerate(similarity_matrix))
    print('similarity_score: ', len(similarity_score))
    # Sort the Above List of Tuples by The Similarity Score in Descendant Order
    similarity_score = heapq.nlargest(num_rec+1, similarity_score, key=lambda tup: tup[1])
    # Get the Titles of the Recommended Accommodation
    Acc_indices = [item[0] for item in similarity_score[1:]]
    return acc_list_df.iloc[Acc_indices]

def recommend(request):
    # Load The Accommodation data and user_profile_vector
    data, user_profile_vector, acc_list = cb_loadData(request)
    similarity = cosSimilarity(data, user_profile_vector)
    print('shape: ', len(data), len(user_profile_vector))
    print('similarity: ', len(similarity))
    # Generate Recommended Accommodations
    recommendation = recForOneItem(acc_list, similarity, 20)
    print("Recommendation List:")
    print(recommendation)
    return recommendation
##===========================
# Recommendation model end
##===========================


def gen_token():
    token = secrets.token_hex(32)
    while Account.objects.filter(curr_token = token):
        token = secrets.token_hex(32)
    return token

##===========================
# Generate the file name for each 
# photo to store on google cloud
##===========================
def generate_filename(prefix, suffix):
    file_idx = secrets.token_hex(32)
    while default_storage.exists(prefix + '_' + file_idx + suffix):
        file_idx = secrets.token_hex(32)
    return prefix + '_'  + file_idx + suffix

##=====================================
# Varify whether the user have logined
# to check the session of request
##=====================================
def get_username_by_session(request):
    if 'username' in request.session and 'token' in request.session and request.session['username'] != "" and request.session != ['token']:
        token = request.session['token']
        username = request.session['username']
        if token == Account.objects.get(username=username).curr_token:
            return username
    return None

##=====================================
# Varify whether the user have logined
# to check the session of request
##=====================================
def get_basic_nums_at_profile(request):
    username = get_username_by_session(request)
    data = {}
    if username:
        user = Account.objects.get(username=username)
        portrait_address = user.portrait_address
        listing_num = Accommodation.objects.filter(owner_id=user).count()
        booking_num_as_visitor = Order.objects.filter(username=user).count()
        booking_num_from_visitor = Order.objects.filter(accommodation_id__in=Accommodation.objects.filter(owner_id=user)).count()
        booking_num = booking_num_as_visitor + booking_num_from_visitor
        count_listing = Accommodation.objects.filter(owner_id=user).count()
        count_active = Accommodation.objects.filter(owner_id=user).filter(is_public=True).count()
        count_pending = Accommodation.objects.filter(owner_id=user).filter(is_public=False).count()
        count_requests = Request.objects.filter(owner_id=user).count()
        count_pending_request = Request.objects.filter(owner_id=user).filter(is_public=False).count()
        count_active_request = Request.objects.filter(owner_id=user).filter(is_public=True).count()
        count_reviews_from_guests = Review.objects.filter(acc_owner_id=user).count()
        count_my_replies = Review.objects.filter(reviewer_id=user).count()
        reviews_num = count_reviews_from_guests + count_my_replies
        data = {
            "listing_num": json.dumps(listing_num),
            "booking_num": json.dumps(booking_num),
            "booking_num_from_visitor": json.dumps(booking_num_from_visitor),
            "booking_num_as_visitor": json.dumps(booking_num_as_visitor),
            "reviews_num": json.dumps(reviews_num),
            "show_img": portrait_address,
            "count_listing": json.dumps(count_listing),
            "count_active": json.dumps(count_active),
            "count_pending": json.dumps(count_pending),
            "count_requests": json.dumps(count_requests),
            "count_active_request": json.dumps(count_active_request),
            "count_pending_request": json.dumps(count_pending_request),
            "count_reviews_from_guests":json.dumps(count_reviews_from_guests),
            "count_my_replies": json.dumps(count_my_replies)
        }
    return data

##==========================================
# in database the location store as pattern:
# (latitude, longitude)
##==========================================
def formalize_latlng(latlng):
    latlng = latlng.replace("(","")
    latlng = latlng.replace(")","")
    latlng = latlng.replace(" ","")
    latlng_list = latlng.split(",")
    if latlng_list[0] != "" and  latlng_list[1] != "":
        return float(latlng_list[0]), float(latlng_list[1])
    else:
        return None, None

##==============================
# Hide card number for security
##==============================
def hide_card_number(card_number):
    card_list = card_number.split('-')
    for i in range(1,len(card_list)-1):
        card_list[i] = re.sub("\d","*",card_list[i])
    return ' '.join(card_list)

##======================================================
# Encode address to lattitude and longitude,
# or decode latitude and longitude to address or location suburb
##======================================================
def trans_latlng_and_address(input, message):
    try:
        ctx = ssl.create_default_context(cafile=certifi.where())
        geopy.geocoders.options.default_ssl_context = ctx
        geolocator = Nominatim(timeout=3)
        if message == 'latlng_to_address':
            latlng = input.replace("(","")
            latlng = latlng.replace(")","")
            location = geolocator.reverse(latlng)
            return location.address
        if message == 'get_suburb':
            latlng = input.replace("(","")
            latlng = latlng.replace(")","")
            location = geolocator.reverse(latlng)
            return location.raw['address']['city']
        if message == 'address_to_latlng':
            print(input)
            latlng = geolocator.geocode(input)
            return latlng.latitude, latlng.longitude
        return None
    except GeocoderTimedOut:
        return trans_latlng_and_address(input, message)

def save_history(username, accommodation, role):
    user = Account.objects.get(username=username)
    ret = UserHistory.objects.filter(owner_id=user).filter(accommodation_id=accommodation)
    print('history ret: ', ret)
    if role == 'history':
        if len(ret) == 0:
            UserHistory.objects.create(owner_id=user, accommodation_id=accommodation, is_history=True)
        else:
            if ret[0].is_favourite == False:
                ret.update(is_history=True, time=django.utils.timezone.now())
    elif role == 'favourite':
        if len(ret) == 0:
            UserHistory.objects.create(owner_id=user, accommodation_id=accommodation, is_favourite=True)
        else:
            if ret[0].is_favourite == False:
                ret.update(is_favourite=True, time=django.utils.timezone.now())
    elif role == 'undo':
        if len(ret) != 0:
            if ret[0].is_favourite == True:
                ret.update(is_favourite=False, time=django.utils.timezone.now())

##====================================================================
# This file similar to the schema of relational database
# each class represent a table in the database
# the attributes of each class is same as columns of table
##====================================================================

from django.db import models
import djongo.models as mongoModels
import datetime

# Create your models here.

class AccommodationAlbum(mongoModels.Model):
    accommodation_id = mongoModels.IntegerField()
    urls = mongoModels.TextField()
    class Meta:
        app_label = 'mongo'
        #db_table = 'AccommodationAlbum'

class ReviewsAlbum(mongoModels.Model):
    review_id = mongoModels.IntegerField()
    username = mongoModels.CharField(max_length=20, default="")
    urls = mongoModels.TextField()
    class Meta:
        app_label = 'mongo'

class Account(models.Model):
    username = models.CharField(unique=True,max_length=50)
    name = models.CharField(max_length=50, default="")
    password = models.CharField(max_length=22)
    email = models.EmailField(default="")
    description = models.TextField()
    url = models.URLField(default="")
    portrait_address = models.URLField(default="")
    curr_token = models.CharField(max_length=50)
    favourite = models.TextField(max_length=200, default="")
    history = models.TextField(max_length=200, default="")

class Accommodation(models.Model):
    physical_address = models.CharField(max_length=100, default="")
    create_time = models.DateTimeField(auto_now_add=True)
    update_time = models.DateTimeField(auto_now=True)
    owner_id = models.ForeignKey(Account, on_delete=models.CASCADE)
    title = models.CharField(max_length=50, default="")
    description = models.TextField(default="")
    property_type = models.CharField(max_length=20, default="")
    property_size = models.CharField(max_length=20, default="")
    dedicated_guests = models.BooleanField(default=False)
    guests_num = models.IntegerField(default=0)
    bedrooms_num = models.IntegerField(default=0)
    beds_num = models.IntegerField(default=0)
    bathrooms_num = models.IntegerField(default=0)
    location = models.CharField(max_length=100, default="")
    album_address = models.URLField(default="")
    is_public = models.BooleanField(default=False)
    is_new_listing = models.BooleanField(default=False)
    avg_rating = models.FloatField(default=0) 
    star_rating = models.FloatField(default=0)
    price = models.FloatField(default=0) 
    picts_num = models.IntegerField(default=0)
    reviews_num = models.IntegerField(default=0)
    can_instant_book = models.BooleanField(default=False)
    city = models.CharField(max_length=30, default="")
    neighborhood = models.CharField(max_length=50, default="")
    url = models.URLField(default="")

class Amenity(models.Model):
    accommodation_id = models.ForeignKey(Accommodation, on_delete=models.CASCADE)
    essentials = models.TextField(default=False)
    air_conditioning = models.BooleanField(default=False)
    heat = models.BooleanField(default=False)
    hair_dryer = models.BooleanField(default=False)
    closet = models.BooleanField(default=False)
    iron = models.BooleanField(default=False)
    tv = models.BooleanField(default=False)
    fireplace = models.BooleanField(default=False)
    private_entrance = models.BooleanField(default=False)
    shampoo = models.BooleanField(default=False)
    wifi = models.BooleanField(default=False)
    workspace = models.BooleanField(default=False)
    breakfast = models.BooleanField(default=False)

class Share_space(models.Model):
    accommodation_id = models.ForeignKey(Accommodation, on_delete=models.CASCADE)
    kitchen = models.BooleanField(default=False)
    washing_machine = models.BooleanField(default=False)
    dryer = models.BooleanField(default=False)
    parking = models.BooleanField(default=False)
    gym = models.BooleanField(default=False)
    pool = models.BooleanField(default=False)
    hot_tub = models.BooleanField(default=False)
    lift = models.BooleanField(default=False)

class Order(models.Model):
    username = models.ForeignKey(Account, on_delete=models.CASCADE)
    accommodation_id = models.ForeignKey(Accommodation, on_delete=models.CASCADE)
    check_in = models.DateField()
    check_out = models.DateField()
    guests_num = models.IntegerField(default=0)
    card_number = models.CharField(max_length=30,default="")
    expiry_month = models.IntegerField(default=0)
    expiry_year = models.IntegerField(default=0)
    cvv = models.IntegerField(default=0)
    total_price = models.FloatField(default=0)
    order_time = models.DateTimeField(default=datetime.datetime.now)
    status = models.CharField(max_length=30,default="")

class Review(models.Model):
    accommodation_id = models.ForeignKey(Accommodation, on_delete=models.CASCADE)
    acc_owner_id = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='owner_id')
    date = models.DateField(default=datetime.date.today)
    reviewer_id = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='reviewer_id')
    reviewer_name = models.CharField(max_length=50,default="")
    like = models.IntegerField(default=0)
    score = models.FloatField(default=0)
    comments = models.TextField(default="")

class Comment(models.Model):
    review_id = models.ForeignKey(Review, on_delete=models.CASCADE)
    acc_owner_id = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='owner')
    accommodation_id = models.ForeignKey(Accommodation, on_delete=models.CASCADE)
    reply_to = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='reply_to_user')
    username = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='comment_user')
    content = models.TextField(default="")
    comment_time = models.DateTimeField(default=datetime.datetime.now)
    like = models.IntegerField(default=0)
    album_address = models.URLField(default="")

class Request(models.Model):
    owner_id = models.ForeignKey(Account, on_delete=models.CASCADE)
    is_public = models.BooleanField(default=False)
    title = models.CharField(max_length=50, default="")
    property_type = models.CharField(max_length=20, default="")
    city = models.CharField(max_length=30, default="")
    guests_num = models.IntegerField(default=0)
    bedrooms_num = models.IntegerField(default=0)
    beds_num = models.IntegerField(default=0)
    bathrooms_num = models.IntegerField(default=0)
    price = models.FloatField(default=0) 
    air_conditioning = models.BooleanField(default=False)
    wifi = models.BooleanField(default=False)
    tv = models.BooleanField(default=False)
    washing_machine = models.BooleanField(default=False)
    kitchen = models.BooleanField(default=False)
    parking = models.BooleanField(default=False)
    gym = models.BooleanField(default=False)
    description = models.TextField(default="")

class UserHistory(models.Model):
    owner_id = models.ForeignKey(Account, on_delete=models.CASCADE)
    accommodation_id = models.ForeignKey(Accommodation, on_delete=models.CASCADE)
    is_history = models.BooleanField(default=False)
    is_favourite = models.BooleanField(default=False)
    time = models.DateTimeField(default=datetime.datetime.now)

class RequestReview(models.Model):
    request_id = models.ForeignKey(Request, on_delete=models.CASCADE)
    request_owner_id = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='request_owner')
    request_time = models.DateTimeField(default=datetime.datetime.now)
    reply_id = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='reply_id')
    reply_name = models.CharField(max_length=50,default="")
    like = models.IntegerField(default=0)
    comments = models.TextField(default="")

class RequestComment(models.Model):
    rq_review_id = models.ForeignKey(RequestReview, on_delete=models.CASCADE)
    request_owner_id = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='rq_owner')
    request_id = models.ForeignKey(Request, on_delete=models.CASCADE)
    reply_to = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='rq_reply_to_user')
    username = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='rq_comment_user')
    content = models.TextField(default="")
    comment_time = models.DateTimeField(default=datetime.datetime.now)
    like = models.IntegerField(default=0)

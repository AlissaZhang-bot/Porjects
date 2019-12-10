from django.contrib import admin
from .models import Account, Accommodation, Amenity, Share_space, Order, Review, Comment, Request
# Register your models here.

admin.site.register(Account)
admin.site.register(Accommodation)
admin.site.register(Amenity)
admin.site.register(Share_space)
admin.site.register(Order)
admin.site.register(Review)
admin.site.register(Comment)
admin.site.register(Request)
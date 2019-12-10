##===================================================
# This file used for store crawled data into database 
# and fill the empty colum to ensure data integration
##===================================================

from .models import Accommodation, Account, AccommodationAlbum
from django.core.files.storage import default_storage
import json
import os
from random import randint
import re
from .utils import generate_filename
import requests
from collections import defaultdict

# load json data from file
def load():
    with open('../airbnb_crawl/crawl.json','r') as f:
        data = json.load(f)
        return data
##================================
# batch load data into database
##================================
def update_accommodation_info():
    info = load()
    listings = []
    for _ in info:
        listing_url = _['url']
        listings.append(listing_url)
        listing = None
        try:
            listing = Accommodation.objects.using('default').get(url=listing_url)
        except Accommodation.DoesNotExist:
            listing = Accommodation(url=listing_url)
        accommodation_id = listing.id
        #owner_id = models.ForeignKey(Account, on_delete=models.CASCADE)
        listing.owner_id = Account.objects.using('default').get(username='Alice1')
        listing.title = _['listing_name']
        #listing.description = listing_name
        listing.property_type = _['room_and_property_type']
        listing.property_size = _['room_type_category']
        #listing.dedicated_guests = _['']
        listing.guests_num = _['person_capacity']
        listing.bedrooms_num = _['bedrooms']
        listing.beds_num = _['num_beds']
        listing.bathrooms_num = _['bathrooms']
        #listing.location = _['']
        #listing.album_address = _['']
        listing.is_public = True
        listing.is_new_listing = _['is_new_listing']
        listing.avg_rating = _['avg_rating']
        listing.star_rating = _['star_rating'] if _['star_rating'] else 0
        listing.price = _['price']
        #lisitng.picts_num = _['']
        listing.reviews_num = _['reviews_count']
        listing.can_instant_book = _['can_instant_book']
        listing.city = _['localized_city']
        listing.neighborhood = _['localized_neighborhood'] if _['localized_neighborhood'] else 0
        listing.save()

        try:
            print("exist")
            listing_imgs = AccommodationAlbum.objects.using('db1').get(accommodation_id=accommodation_id)
        except AccommodationAlbum.DoesNotExist:
            print("new")
            listing_imgs = AccommodationAlbum.objects.using('db1').create(accommodation_id=accommodation_id)
        listing_imgs.urls = _['picture_urls']
        print("type of listing_imgs: ", type(listing_imgs))
        listing_imgs.save(using='db1')

##====================================
# download the images from crawled url
##====================================
def download_accommodation_images():
    info = load()
    for i in range(len(info)):
        download_urls = info[i]['picture_urls']
        if not os.path.exists('../airbnb_crawl/images'):
            os.makedirs('../airbnb_crawl/images')
        for download_url in download_urls:
            file_name = generate_filename('../airbnb_crawl/images/accommodation'+str(i+1), '.jpg')
            f = requests.get(download_url)
            with open(file_name,'wb') as code:
                code.write(f.content)
            code.close()

##==================================================================
# upload images to Google Cloud Storage and store the url to mongoDB
##==================================================================
def upload_accommodation_images():
    # read image files from local documents
    file_list = os.listdir('../airbnb_crawl/images')
    for image_file in file_list:
        regex = re.compile('^accommodation\d+_')
        accommodation_id = int(regex.match(image_file).group()[13:-1])
        with open('../airbnb_crawl/images/'+image_file,'rb') as load_f:
            content = load_f.read()
        load_f.close()
        file = default_storage.open(image_file, 'wb')
        file.write(content)
        file.close()
        print(image_file+"has been writen to google cloud")
        try:
            print("exist")
            listing_imgs = AccommodationAlbum.objects.using('db1').get(accommodation_id=accommodation_id)
        except AccommodationAlbum.DoesNotExist:
            print("new")
            listing_imgs = AccommodationAlbum.objects.using('db1').create(accommodation_id=accommodation_id)
        
        urls_str = listing_imgs.urls.replace("'",'"')
        urls_list = json.loads(urls_str)
        urls_list.append('https://storage.cloud.google.com/accomodation9900_property_images/'+image_file)
        listing_imgs.save(using='db1')
    

def save_accommodation_images_urls():
    file_list = os.listdir('../airbnb_crawl/images')
    with open ('../image_filenames.txt', 'w') as f:
        f.write(json.dumps(file_list))
    f.close()
    """ for image_file in file_list:
        regex = re.compile('^accommodation\d+_')
        accommodation_id = int(regex.match(image_file).group()[13:-1])
        print(image_file, accommodation_id)
        try:
            print("exist")
            listing_imgs = AccommodationAlbum.objects.using('db1').get(accommodation_id=accommodation_id)
        except AccommodationAlbum.DoesNotExist:
            print("new")
            listing_imgs = AccommodationAlbum.objects.using('db1').create(accommodation_id=accommodation_id)
        urls_str = listing_imgs.urls.replace("'",'"')
        urls_list = json.loads(urls_str)
        urls_list.append('https://storage.cloud.google.com/accomodation9900_property_images/'+image_file)
        listing_imgs.urls = urls_list
        listing_imgs.save(using='db1') """

##====================================
# Download the images from crawled url
##====================================
def modify_album_url():
    file_list = os.listdir('../airbnb_crawl/images')
    accommodations = defaultdict(str)
    i = 1
    for file in file_list:
        if accommodations[i]:
            continue
        regex = re.compile('^accommodation'+ str(i) +'+_')
        if regex.match(file):
            accommodations[i] = file
            a = Accommodation.objects.get(id=i)
            a.album_address = 'https://storage.cloud.google.com/accomodation9900_property_images/'+file
            a.save()
            i += 1
            if i == 132:
                break

##====================================
# Download the images from crawled url
##====================================
def modify_location():
    info = load()
    for i in range(1,133):
        accommodation = Accommodation.objects.get(id=i)
        accommodation.location = str((info[i-1]['lat'], info[i-1]['lng']))
        accommodation.save()

def test():
    try:
        print("exist")
        listing_imgs = AccommodationAlbum.objects.using('db1').get(accommodation_id=123)
    except AccommodationAlbum.DoesNotExist:
        print("new")
        listing_imgs = AccommodationAlbum.objects.using('db1').create(accommodation_id=123)
        print("already create")
        listing_imgs.save(using='db1')
    urls_str = listing_imgs.urls.replace("'",'"')
    urls_list = json.loads(urls_str)
    urls_list.append('https://storage.cloud.google.com/accomodation9900_property_images/accommodation123_025d371d371c05486f717a0209e2c401dde65b9f68ded215fe4cfe44f63980d8.jpg')
    listing_imgs.urls = urls_list
    listing_imgs.save(using='db1')

##=========================================================================
# pick random images from Google Cloud Storage and store the url to mongoDB
##=========================================================================
def store_random_accommodation_images():
    ### read image files from local documents
    with open (r"../airbnb_crawl/image_filenames.txt","r") as f:
        lineList = f.readline().split(',')
    length = len(lineList)
    photo_num = randint(4,6)

    for id in range(133, 1844):
        print("processed: ", id)
        urls_list = []
        num = AccommodationAlbum.objects.using('db1').filter(accommodation_id=id).count()
        if num == 1:
            listing_imgs = AccommodationAlbum.objects.using('db1').get(accommodation_id=id)
            listing_imgs.urls = []
        elif num == 0:
            listing_imgs = AccommodationAlbum.objects.using('db1').create(accommodation_id=id, urls="")
        else :
            AccommodationAlbum.objects.using('db1').filter(accommodation_id=id).delete()
            listing_imgs = AccommodationAlbum.objects.using('db1').create(accommodation_id=id, urls="")
        for i in range(photo_num):
            r = randint(1, length-2)
            
            add = lineList[r].replace(' ','')
            add = add.replace('\"','')

            urls_list.append('https://storage.cloud.google.com/accomodation9900_property_images/'+add)
            
        listing_imgs.urls = urls_list
        listing_imgs.save(using='db1')

##===============================================
# set random guests number for each accommodation
##===============================================
def set_guests_bedrooms_num():
    for id in range(1, 1844):
        accommodation = Accommodation.objects.get(id=id)
        if accommodation.beds_num == 0:
            accommodation.beds_num = randint(1,6)
        if accommodation.bedrooms_num == 0:
            accommodation.bedrooms_num = randint(1,accommodation.beds_num)
        if accommodation.guests_num == 0:
            accommodation.guests_num = randint(2,6)
        accommodation.save()

if __name__ == '__main__':
    #update_accommodation_info()
    #download_accommodation_images()
    #upload_accommodation_images()
    #test()
    #save_accommodation_images_urls()
    #modify_album_url()
    #modify_location()
    set_guests_bedrooms_num()
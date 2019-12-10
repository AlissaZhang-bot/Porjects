import json
import collections
import re
import numpy as np
import logging
import sys
import scrapy
from scrapy_splash import SplashRequest
from scrapy.exceptions import CloseSpider

# *********************************************************************************************
# Run crawler with -> scrapy crawl airbnb_amenity -o amenity.json                             *
# Since I need to read a crawl.json file, might need to change path to the file               *
# depends on where i run this command                                                         *
# *********************************************************************************************

# this file is to keep running into accommodation pages to crawl information about
# amenity and reviews

class AirbnbSpider(scrapy.Spider):
    name = 'airbnb_amenity'
    allowed_domains = ['www.airbnb.com.au']

    def __init__(self, city='',*args,**kwargs):
        super(AirbnbSpider, self).__init__(*args, **kwargs)
        self.city = city

    # this function is to generate url for every web link in crawl.json file
    # return a url list to start_requests function
    def generate_urls(self):
        with open('./crawl.json','r') as f:
            data = json.load(f)
        room_ids = []
        for item in data:
            url = item['url']
            room_id = url.split('/')[4]
            print(room_id)
            room_ids += [int(room_id)]
            #print(room_id)
        print(room_ids)
        return room_ids


    def start_requests(self):
        '''Sends a scrapy request to the designated url price range
        Args:
        Returns:
        '''
        for room_id in self.generate_urls():
            url = ('https://www.airbnb.com.au/api/v2/pdp_listing_details/'
                    '{0}?_format=for_rooms_show&key=d306zoyjsyarp7ifhu67rjxn52tv0t20&')
            new_url = url.format(str(room_id))
            yield scrapy.Request(url=new_url, callback=self.parse_id, dont_filter=True)


    def parse_id(self, response):
        '''Parses all the URLs/ids/available fields from the initial json object and stores into dictionary
        Args:
            response: Json object from explore_tabs
        Returns:
        '''    
        # Fetch and Write the response data
        data = json.loads(response.body)

        # Return a List of all amenities from one webpage
        base_url = 'https://www.airbnb.com.au/rooms/'
        room_id = data.get('pdp_listing_detail').get('id')
        url = base_url + room_id
        amenities = []
        for item in data.get('pdp_listing_detail').get('listing_amenities'):
            for listing in item:
                homes += listing.get('name')
        print(url, amenities)

        data_dict = collections.defaultdict(dict) # Create Dictionary to put all currently available fields in
        data_dict[room_id][amenities] = amenities

        # Iterate through dictionary of URLs in the single page to send a SplashRequest for each
        yield SplashRequest(url=base_url+room_id, callback=self.parse_details,
                                meta=room_id,
                                endpoint="render.html",
                                args={'wait': '0.5'})


    def parse_details(self, response):
        '''Parses details for a single listing page and stores into AirbnbScraperItem object
        Args:
            response: The response from the page (same as inspecting page source)
        Returns:
            An AirbnbScraperItem object containing the set of fields pertaining to the listing
        '''
        # New Instance
        listing = AirbnbCrawlItem()

        # Fill in fields for Instance from initial scrapy call
        listing['room_id'] = response.meta['room_id']
        listing['amenities'] = str(response.meta['amenities'])

        # Finally return the object
        yield listing


class AirbnbCrawlItem(scrapy.Item):
    room_id = scrapy.Field()
    amenities = scrapy.Field()
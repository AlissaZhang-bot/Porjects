Run crawler with -> 
    scrapy crawl auto_airbnb -o crawl.json -a city='Sydney'
This is to get basic information about the properties in Sydney on the searching page.
There ia already an existed crawl.json file.
However it only provides amentity ids instead of exact name of amenities,
we need to crawl on the exact page of the property to get more information.
That is to run crawler with
    scrapy crawl airbnb_amenity -o amenity.json  
Also note that too many trials would be blocked by Airbnb.
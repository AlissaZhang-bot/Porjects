import json
import time
import pprint
import collections

with open('first_page.json', 'rb') as file:
    data = json.load(file)

#homes = data.get('explore_tabs')[0].get('sections')[1].get('listings')
homes = []
for item in data.get('explore_tabs')[0].get('sections'):
    if item.get('listings'):
        print(len(item.get('listings')))
        homes += item.get('listings')
print(len(homes))

BASE_URL = 'https://www.airbnb.com.au/rooms/'
data_dict = collections.defaultdict(dict)
for home in homes:
    room_id = str(home.get('listing').get('id'))
    #print('room_id: ', room_id)
    data_dict[room_id]['city'] = home.get('listing').get('city')
    data_dict[room_id]['nb_bathrooms'] = home.get('listing').get('bathrooms')
    data_dict[room_id]['nb_bedrooms'] = home.get('listing').get('bedrooms')
    data_dict[room_id]['nb_beds'] = home.get('listing').get('beds')
    data_dict[room_id]['guest_label'] = home.get('listing').get('guest_label')
    data_dict[room_id]['host_languages'] = home.get('listing').get('host_languages')
    data_dict[room_id]['url'] = BASE_URL + str(home.get('listing').get('id'))
    data_dict[room_id]['price'] = home.get('pricing_quote').get('rate').get('amount')
    data_dict[room_id]['avg_rating'] = home.get('listing').get('avg_rating')
    data_dict[room_id]['reviews_count'] = home.get('listing').get('reviews_count')

print(data_dict.keys())
# printer = pprint.PrettyPrinter()
# printer.pprint(data_dict)

def parse(response):
    _file = "accommodation.json"
    with open(_file, 'w+') as f:
        f.write(json.dumps(response))
        
parse(homes)
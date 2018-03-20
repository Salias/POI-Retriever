import time
import sys
import os
import json
import requests
import codecs
import foursquare
import pandas as pd
import numpy as np
import logging

from create_grid import make_grid
from settings import *

CITY = sys.argv[1]
logging.basicConfig(level=logging.INFO)
HEADER = [
                            'key', 'name', 'address', 'city',
                            'state', 'country', 'postal', 'sic_code', 'side_street', '_id',
                            'x', 'y',
                            'lon', 'lat']

class POIRetriever(object):

    def __init__(self, output_path):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.output_path = output_path

        if not os.path.exists(self.output_path):
            os.makedirs(self.output_path)

        try:
            track = open(self.output_path+'/ids.txt', 'r')
            self.ids = [i.rstrip() for i in track]
            track.close()
        except IOError:
            self.ids = []

        try:
            track = open(self.output_path+'/processed.txt', 'r')
            self.processed = [i.rstrip() for i in track]
            track.close()
        except IOError:
            self.processed = []

        boxes = pd.read_csv(FILES_PATH+'/boundboxes.txt', sep='\t')
        city_box = boxes[boxes['city'].str.lower() == CITY]

        if city_box.shape[0] == 0:
            print 'Cannot find city bounding box'
            exit()
        elif city_box.shape[0] > 1:
            print 'The city is duplicated in boundboxes.txt'
            exit()
        else:
            try:
                print 'Loading GRID for ', CITY
                self.grid = pd.read_csv(FILES_PATH+'/grids/'+CITY+'.csv')
            except:
                print 'Creating GRID for ', CITY
                BOUNDBOX = city_box[['lon1', 'lat1', 'lon2', 'lat2']].values[0]
                self.grid = make_grid(BOUNDBOX, 10)
                self.grid.to_csv(FILES_PATH+'/grids/'+CITY+'.csv', index=False)
                print 'Done!'

    def _set_params(self, key, x, y):
        return None

    def _request(self, params):
        if params is None:
            raise Exception('No parameters to request..'+__name__)

        try:
            r = requests.get(self.domain, params=params)
        except Exception, e:
            self.logger.error("Failed to to request...", exc_info=True)
            return -1

        if r.status_code == 200:
            return r.content
        else:
            return -1

    def query(self, x, y):
        DONE = False
        attempts = 0
        while not DONE or attempts < len(self.KEYS)+1:
            key = next(self.KEYS_ITER)
            params = self._set_params(key, x, y)
            response = self._request(params)
            if response != -1:
                return response
                DONE = True
            else:
                self.logger.info('Request Failed ! Changing keys.......')
                key = next(self.KEYS_ITER)
                attempts += 1

    def save_line(self, _id, line):
        out = ','.join(line)
        with codecs.open(self.dataset_path, 'a', encoding='utf8') as dataset:
            dataset.write(out+'\n')
        with open(self.output_path+'/ids.txt', 'a') as track:
            self.ids.append(_id)
            track.write(_id+'\n')

        msg = "New Venue ! -> "+line[1]
        self.logger.info(msg)

    def run(self):
        try:
            while True:
                print 'NEW ROUND !!!!'
                for index, x, y in self.grid.values:
                    response = self.query(x, y)
                    if response is not None:
                        self.save((x, y), index, response)
                        with open(self.output_path+'/processed.txt', 'a') as track:
                            self.processed.append(index)
                            track.write(str(index)+'\n')

        except KeyboardInterrupt:
            with open(self.output_path+'/ids.txt', 'w') as track:
                for _id in self.ids:
                    track.write(_id+'\n')
            self.logger.info("Checkpoints Saved")

class BingRetriever (POIRetriever):

        def __init__(self, output_path=DATA_PATH+'/'+CITY+'/bing'):
            super(BingRetriever, self).__init__(output_path)
            self.output_path = output_path
            self.dataset_path = self.output_path+'/bing.csv'
            self.domain = 'http://spatial.virtualearth.net/REST/v1/data/f22876ec257b474b82fe2ffcb8393150/NavteqNA/NavteqPOIs'
            self.sic = pd.read_csv(FILES_PATH+'/sic.csv')
            self.KEYS = BING_KEYS
            self.KEYS_ITER = BING_KEYS_ITER

        def _get_sic_name(self, _id):
            try:
                return self.sic[sic['EntityID'] == int(_id)]['EntityName'].values[0]
            except:
                return ''

        def _set_params(self, key, x, y):
            lon, lat = (x, y)
            return {
                'key': key['key'],
                'spatialFilter': "nearby(%f, %f, %d)" % (lat, lon, 1),
                '$format': 'json'
            }

        def save(self, origin, index, response):
            x, y = origin
            data = json.loads(response)['d']['results']
            for venue in data:
                name = venue['DisplayName'].replace(',', ' ')
                lon = venue['Longitude']
                lat = venue['Latitude']
                address = venue['AddressLine'].replace(',', ' ')
                city = venue['AdminDistrict2'].replace(',', ' ')
                state = venue['AdminDistrict']
                country = venue['CountryRegion']
                postal = venue['PostalCode']
                sic_code = venue['EntityTypeID']
                sic_name = self._get_sic_name(sic_code)
                _id = venue['EntityID']
                line = [
                            _id, name, address, city,
                            state, country, postal, sic_code, sic_name, _id,
                            str(x), str(y),
                            str(lon), str(lat),
                       ]

                self.save_line(_id, line)

class MapQuestRetriever (POIRetriever):

        def __init__(self, output_path=DATA_PATH+'/'+CITY+'/mapquest'):
            super(MapQuestRetriever, self).__init__(output_path)
            self.output_path = output_path
            self.dataset_path = self.output_path+'/mapquest.csv'
            self.domain = 'http://www.mapquestapi.com/search/v2/radius'
            self.KEYS = MAPQUEST_KEYS
            self.KEYS_ITER = MAPQUEST_KEYS_ITER

        def _set_params(self, key, x, y):
            lon, lat = (x, y)
            return {
                'key': key['consumer_key'],
                'maxMatches': '50',
                'radius': 1,
                'units': 'km',
                'origin': ','.join([str(lat), str(lon)])
            }

        def save(self, origin, index, response):
            x, y = origin
            try:
                data = json.loads(response)['searchResults']
                for venue in data:
                    name = venue['name'].replace(',', ' ')
                    lat, lon = venue['shapePoints']
                    address = venue['fields']['address'].replace(',', ' ')
                    city = venue['fields']['city'].replace(',', ' ')
                    state = venue['fields']['state']
                    country = venue['fields']['country']
                    postal = venue['fields']['postal_code']
                    sic_code = venue['fields']['group_sic_code_name']
                    side_street = venue['fields']['side_of_street']
                    _id = venue['fields']['id']
                    line = [
                                venue['key'], name, address, city,
                                state, country, postal, sic_code, side_street, _id,
                                str(x), str(y),
                                str(lon), str(lat),
                           ]

                    self.save_line(venue['key'], line)
            except KeyError:
                pass

class FourSquareRetriever (POIRetriever):

    def __init__(self, output_path=DATA_PATH+'/'+CITY+'/foursquare'):
        super(FourSquareRetriever, self).__init__(output_path)
        self.key = next(FOURSQUARE_KEYS_ITER)
        self.output_path = output_path
        self.dataset_path = self.output_path+'/venues.csv'
        self.client = foursquare.Foursquare(client_id=self.key['client_id'], client_secret=self.key['client_secret'])

    def save(self, origin, index, response):
        for element in response['groups']:
            for item in element['items']:
                _id = item['venue']['id']
                venue = item['venue']
                if _id not in self.ids:
                    if 'address' in venue['location']:
                        address = venue['location']['address']
                    else:
                        address = ''

                    if 'city' in venue['location']:
                        city = venue['location']['city']
                    else:
                        city = ''

                    country = venue['location']['cc']
                    category = venue['categories'][0]['name']
                    category_id = venue['categories'][0]['id']
                    line = [
                                venue['id'], venue['name'], address,
                                city, country, category_id, category,
                                str(origin[0]), str(origin[1]),
                                str(venue['location']['lng']), str(venue['location']['lat'])
                           ]
                    self.save_line(_id, line)

    def query(self, x, y):
        while True:
            try:
                return self.client.venues.explore({'ll': '%f,%f' % (y, x), 'radius': 1000*10, 'limit': 50})
            except foursquare.FoursquareException:
                self.logger.info('Rate Limit Exceeded: waiting 1 hour')
                time.sleep(60*60*60)


if __name__ == '__main__':
    # MapQuestRetriever().run()
    import multiprocessing as mp

    jobs = [('mapquest', MapQuestRetriever().run), ('foursquare', FourSquareRetriever().run), ('bing', BingRetriever().run)]
    processes = []
    for name, job in jobs:
        n = mp.Process(name=name, target=job)
        n.daemon = False
        processes.append(n)
        n.start()

    for processe in processes:
        processe.join()

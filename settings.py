from itertools import cycle

DATA_PATH = 'data'
FILES_PATH = 'files'
HOURLY_LIMIT = 5000


# https://developer.foursquare.com/docs/api/getting-started
FOURSQUARE_KEYS = [
						{'client_id': '', 'client_secret': ''}
				  ]
FOURSQUARE_KEYS_ITER = cycle(FOURSQUARE_KEYS)

#MAPQUEST https://developer.mapquest.com/
# https://developer.mapquest.com/plan_purchase/steps/business_edition/business_edition_free/register
MAPQUEST_KEYS = [
                        {'consumer_key': '', 'consumer_secret': ''},
                        {'consumer_key': '', 'consumer_secret': ''},
                        {'consumer_key': '', 'consumer_secret': ''},
                        {'consumer_key': '', 'consumer_secret': ''},
                        {'consumer_key': '', 'consumer_secret':	''},
                        {'consumer_key': '', 'consumer_secret':	''},
                        {'consumer_key': '', 'consumer_secret':	''}
                ]
MAPQUEST_KEYS_ITER = cycle(MAPQUEST_KEYS)

#BING https://msdn.microsoft.com/en-us/library/ff428642.aspx
BING_KEYS = [
						{'key': ''}
			]
BING_KEYS_ITER = cycle(BING_KEYS)

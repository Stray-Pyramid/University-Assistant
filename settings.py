postgresql_settings = {
	'user': None,
	'password': None,
	'host': None,
	'database':None,
	'sslmode':'require',
	'connect_timeout' : '5'
}

weather = {
	'darksky_api_key' : None,
	'darksky_url' : "https://api.darksky.net/forecast/",
	'metservice_auckland_url' : "http://www.metservice.com/towns-cities/auckland/auckland-central"
}


schedule = {
	'num_of_days' : 7,
	'subject_colours' : {
		"Subject 1": "Red",
		"Subject 2": "Blue",
		"Subject 3": "Green",
		"Subject 4": "Yellow",
		"Subject 5": "Black"
	}
}

from enum import Enum

class tabLabel_status(Enum):
	NORMAL = 0
	NOTICE = 1
	ALERT = 2
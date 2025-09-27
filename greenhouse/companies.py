import os
from typing import List, Set, Dict

_CSV_FILE = os.getcwd() + "/from_frontend_gh_{}_jobs.csv"
_BASE_URL = "https://job-boards.greenhouse.io/embed/job_board?"
_API_URL = "https://job-boards.greenhouse.io/embed/job_app?for={}&token="
_ORG_PARAM = "for={}"
_KEYWORD_PARAM = "&keyword={}"
_LOCATION_PARAM = "&offices%5B%5D={}"
_UNFILTERED_ORGS = { 'airbnb' }
_EXCLUDED_ROLE_KEYWORDS = {
    'senior', 'principal', 'manager', 'staff',
    'sr', 'snr', 'sr.', 'snr.',
    'director', 'lead',
}
_EXCLUDED_LOCATIONS = {
    'usa', 'u.s.a.', 'u.s.a', 'u.s.', 'u.s.', 'us',
    'united states', 'united states of america',
    'india', 'china', 'korea',
}
_LOCATIONS = {
    'airbnb': { },
    'snapmobileinc': { },
    'stripe': {
        'canada': '87006',
        'australia': '87005',
        'singapore': '86997',
        'ireland': '87011',
        'romania': '9008',
        'uk': '87009',
    },
    'lyft': {
        'canada': '4038198002',
        'emea': '4038219002',
    },
}
_DEFAULT_LOCATIONS: Dict[str, Set] = {
    'stripe': {
        'canada', 'ireland', 'dublin', 'toronto',
        'singapore', 'malaysia', 'kuala lumpur',
        'australia', 'sydney', 'new zealand',
        'london', 'romania', 'bucharest',
        'united kingdom', 'paris', 'france',
        'amsterdam', 'netherlands', 'melbourne',
        'remote', 'worldwide', 'global', 'europe',
        'berlin', 'germany', 'stockholm', 'sweden'
    },
    'lyft': {
        'canada', 'emea'
    },
}


class OrgConfig():
    """Configure the properties of which company to scrape. """

    def __init__(self, name: str, keywords: List[str], special_exceptions=False, exclude_senior_roles=False, exclude_unwanted_locations=True):
        """
        :param name: The organization's name, ideally all lowercase.
        :param keywords: A list of core keywords to compose the main search query.
        :param special_exceptions: Flag to not process certain search parameters (only location exception for Airbnb is currently supoorted).
        :param exclude_senior_roles: Flag to allow exclusion of roles in :py:attr:`OrgConfig.get_excluded_locations`
        """
        self._name = name.lower()
        self._org = _ORG_PARAM.format(self._name)
        self._csv_file = _CSV_FILE.format(self._name)
        self._keywords = _KEYWORD_PARAM.format(str().join(k + '%20' for k in keywords))
        self._api_url = _API_URL.format(self._name)
        self._default_locations = _DEFAULT_LOCATIONS.get(self._name if self._name in _DEFAULT_LOCATIONS else 'stripe')
        self._use_exceptions = special_exceptions
        self._exclude_senior_roles = exclude_senior_roles
        self._exclude_unwanted_locations = exclude_unwanted_locations

        _locs = []
        for loc in self._default_locations:
            loc_val = _LOCATIONS[self._name].get(loc.lower())
            if loc_val: 
                _locs.append(_LOCATION_PARAM.format(loc_val))

        self._locations = str().join(_locs)
        self.job_board_url = _BASE_URL + self._org + self._keywords + (self._locations if self._name not in _UNFILTERED_ORGS else '')     
    
    def __str__(self):
        return f"company::{self._name}"

    def get_job_board_url(self):
        return self.job_board_url
    
    def get_api_url(self):
        return self._api_url
    
    def get_csv_file(self):
        return self._csv_file
    
    def get_default_locations(self):
        return self._default_locations
    
    def is_use_exceptions(self):
        return self._use_exceptions
    
    def is_exclude_senior_roles(self):
        return self._exclude_senior_roles
    
    def is_exclude_unwanted_locations(self):
        return self._exclude_unwanted_locations
    
    def get_excluded_roles(self):
        return _EXCLUDED_ROLE_KEYWORDS.copy() if self._exclude_senior_roles else set()
    
    def get_excluded_locations(self):
        return _EXCLUDED_LOCATIONS.copy() if self._exclude_unwanted_locations else set()


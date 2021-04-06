#################################
##### Name: Rui Guo
##### Uniqname: guorui
#################################

from bs4 import BeautifulSoup
import requests
import json
import secrets  # file that contains your API key
import time


class NationalSite:
    '''a national site

    Instance Attributes
    -------------------
    category: string
        the category of a national site (e.g. 'National Park', '')
        some sites have blank category.
    
    name: string
        the name of a national site (e.g. 'Isle Royale')

    address: string
        the city and state of a national site (e.g. 'Houghton, MI')

    zipcode: string
        the zip-code of a national site (e.g. '49931', '82190-0168')

    phone: string
        the phone of a national site (e.g. '(616) 319-7906', '307-344-7381')
    '''

    def __init__(self, category='', name='', address='', zipcode='', phone=''):
        self.category = category
        self.name = name
        self.address = address
        self.zipcode = zipcode
        self.phone = phone

    def info(self):
        return f"{self.name} ({self.category}): {self.address} {self.zipcode}"


def build_state_url_dict():
    ''' Make a dictionary that maps state name to state page url from "https://www.nps.gov"

    Parameters
    ----------
    None

    Returns
    -------
    dict
        key is a state name and value is the url
        e.g. {'michigan':'https://www.nps.gov/state/mi/index.htm', ...}
    '''
    html_text = make_url_request_using_cache("https://www.nps.gov/index.htm", CACHE)
    soup = BeautifulSoup(html_text, 'html.parser')
    menu = soup.find('ul', class_="dropdown-menu SearchBar-keywordSearch")
    state_url_dict = {}
    for state in menu.find_all('li'):
        state_url_dict[state.text.lower()] = "https://www.nps.gov" + state.find('a')['href']
    return state_url_dict


def get_site_instance(site_url):
    '''Make an instances from a national site URL.
    
    Parameters
    ----------
    site_url: string
        The URL for a national site page in nps.gov
    
    Returns
    -------
    instance
        a national site instance
    '''
    html_text = make_url_request_using_cache(site_url, CACHE)
    soup = BeautifulSoup(html_text, 'html.parser')
    title = soup.find("div", class_='Hero-titleContainer clearfix')
    name = title.find(class_="Hero-title").text
    category = title.find('span', class_='Hero-designation').text

    contact = soup.find("div", class_='vcard')
    try:
        address = contact.find('span', itemprop="addressLocality").text + ', ' + contact.find('span',
                                                                                              itemprop="addressRegion").text
    except:
        address = "no address"
    try:
        postcode = contact.find('span', itemprop='postalCode').text.strip()
    except:
        postcode = "no zipcode"
    try:
        phone = contact.find('span', class_="tel").text.strip()
    except:
        phone = "no phone"
    return NationalSite(category, name, address, postcode, phone)


def get_sites_for_state(state_url):
    '''Make a list of national site instances from a state URL.
    
    Parameters
    ----------
    state_url: string
        The URL for a state page in nps.gov
    
    Returns
    -------
    list
        a list of national site instances
    '''
    html_text = make_url_request_using_cache(state_url, CACHE)
    soup = BeautifulSoup(html_text, 'html.parser')
    parks = soup.find('ul', id="list_parks")
    instances = []
    for park in parks.find_all('li', class_='clearfix'):
        href = park.find('h3').find('a')['href']
        url = f'https://www.nps.gov/{href}/index.htm'
        instances.append(get_site_instance(url))
    return instances


def get_nearby_places(site_object):
    '''Obtain API data from MapQuest API.
    
    Parameters
    ----------
    site_object: object
        an instance of a national site
    
    Returns
    -------
    dict
        a converted API return from MapQuest API
    '''
    params = {
        'key': secrets.API_KEY,
        'origin': site_object.zipcode,
        'radius': 10,
        'maxMatches': 10,
        'ambiguities': 'ignore',
        'outFormat': 'json'
    }
    baseurl = "http://www.mapquestapi.com/search/v2/radius"
    response = make_api_request_using_cache(baseurl, params, CACHE)
    return response


def load_cache():
    '''Load cache file

    Returns
    -------
    dict
        cache file
    '''
    try:
        cache_file = open(CACHE_FILE_NAME, 'r')
        cache_file_contents = cache_file.read()
        cache = json.loads(cache_file_contents)
        cache_file.close()
    except:
        cache = {}
    return cache


def save_cache(cache):
    '''Save cache file

    Parameters
    ----------
    cache: dict
        cache file

    Returns
    -------
    none
    '''
    cache_file = open(CACHE_FILE_NAME, 'w')
    contents_to_write = json.dumps(cache)
    cache_file.write(contents_to_write)
    cache_file.close()


def make_url_request_using_cache(url, cache):
    '''Get html from the url using cache

    Parameters
    ----------
    url: string
        url to get
    cache: dict
        cache file

    Returns
    -------
    string
        html content
    '''
    if (url in cache.keys()):  # the url is our unique key
        print("Using cache")
        return cache[url]
    else:
        print("Fetching")
        time.sleep(1)
        response = requests.get(url)
        cache[url] = response.text
        save_cache(cache)
        return cache[url]


def construct_unique_key(baseurl, params):
    ''' constructs a key that is guaranteed to uniquely and
    repeatably identify an API request by its baseurl and params, will ignore the key param

    Parameters
    ----------
    baseurl: string
        The URL for the API endpoint
    params: dict
        A dictionary of param:value pairs

    Returns
    -------
    string
        the unique key as a string
    '''
    key = baseurl
    for k, v in params.items():
        if k != 'key':
            key += f"_{k}_{v}"
    return key


def make_api_request_using_cache(baseurl, params, cache):
    ''' make api request with cache

    Parameters
    ----------
    baseurl: string
        The base url of API request
    params: dict
        API request parameters
    cache: dict
        cache file

    Returns
    -------
    dict
        json returned by API
    '''
    unique_key = construct_unique_key(baseurl, params)
    if unique_key not in cache:
        print("Fetching")
        CACHE[unique_key] = requests.get(baseurl, params).json()
        save_cache(CACHE)
    else:
        print('Using Cache')
    return CACHE[unique_key]


def list_sites(state, sites):
    '''Print the sites in the state

    Parameters
    ----------
    state: string
        the searched state
    sites: list of NationalSite
        the list of sites in the chosen state

    Returns
    -------
    none
    '''
    header = f"List of national sites in {state}"
    print("-" * len(header))
    print(header)
    print("-" * len(header))
    for i, site in enumerate(sites):
        print(f"[{i + 1}] {site.info()}")


def list_places(site, places):
    '''Print the places near the chosen site

    Parameters
    ----------
    site: NationalSite
        The site chosen by user
    places: dict
        json returned by MapQuest API

    Returns
    -------
    none
    '''
    header = f"Places near in {site.name}"
    print("-" * len(header))
    print(header)
    print("-" * len(header))
    for place in places["searchResults"]:
        name = place["name"]
        city = place["fields"].get("city", "no city")
        if city == "":
            city = "no city"
        category = place["fields"].get("group_sic_code_name", "no category")
        if category == "":
            category = "no category"
        address = place.get("address", "no address")
        if address == "":
            address = "no address"
        print(f"- {name} ({category}): {address}, {city}")


CACHE_FILE_NAME = 'cache.json'
CACHE = load_cache()

if __name__ == "__main__":
    state_url_dict = build_state_url_dict()
    list_of_sites = []
    state = 0
    while True:
        if state == 0:
            user_input = input('Enter a state name (e.g. Michigan, michigan) or "exit":').lower()
            if user_input == 'exit':
                break
            if user_input not in state_url_dict:
                print("[Error] Enter proper state name")
                print()
                continue
            state_url = state_url_dict[user_input]
            list_of_sites = get_sites_for_state(state_url)
            list_sites(user_input, list_of_sites)
            state = 1
        elif state == 1:
            user_input = input('Choose the number for detail search or "exit" or "back":')
            if user_input == 'exit':
                break
            if user_input == 'back':
                state = 0
                continue
            if not user_input.isdigit() or int(user_input) <= 0 or int(user_input) > len(list_of_sites):
                print("[Error] Invalid input")
                print()
                state = 1
                continue
            target_site = list_of_sites[int(user_input) - 1]
            if target_site.zipcode == "no zipcode" or target_site.zipcode == "":
                print("[Error] No address info for the selected site")
                print()
                state = 1
                continue
            response = get_nearby_places(target_site)
            list_places(target_site, response)
        else:
            break
    print("Bye!")

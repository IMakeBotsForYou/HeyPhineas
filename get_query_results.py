import googlemaps
from keys import *
from requests import get
import json


class results:
    def __init__(self, r):
        self.results = r

    def get(self):

        data = {}

        for r in results:
            json_vr = r.to_json()
            data[json_vr["id"]] = json_vr

        return self.results

    def sort_by_rating(self):
        def rating(r):
            if r.rating == "N/A":
                return 0
            else:
                return r.rating

        self.results.sort(key=rating)
        return self.get()

    def sort_by_name(self):
        self.results.sort(key=lambda r: r.name)
        return self.get()

    def append(self, item):
        self.results.append(item)

    # def sort_by_distance(self):
    #     self.results.sort(key=lambda r: r.name)


class Result_man:
    def __init__(self, place_id, url, close_to, name, icon, rating, local_phone_number, website, open_periods, location):
        self.id = place_id
        self.name = name
        self.icon = icon
        self.url = url
        self.rating = float(rating) if rating else "N/A"
        # self.rating_count = rating[1]
        self.location = location
        self.local_phone_number = local_phone_number
        self.website = website
        self.images = []
        self.vicinity = close_to
        self.open_periods = open_periods

        # self.fix_open()

    def fix_open(self):
        pass
        # days = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
        # new = {}
        # if not self.open_periods:
        #     return
        #
        # getday = compile(r"/w+")
        # for i, day in enumerate(self.open_periods):
        #     d = getday.search(day).group()
        #     self.open_periods[d] = self.open_periods[i][len(d)+1:]
        # return
        #
        # # for period in self.open_periods:
        # #     for time in period:
        # #
        # #         index = period[time]["day"]
        # #
        # #         correct_day = days[index]
        # #         correct_time = period[time]["time"][:2] +":"+ period[time]["time"][2:]
        # #
        # #         if time == "closed":
        # #             new[correct_day] = {"closed": correct_time, "open": None}
        # #         else:
        # #             new[correct_day] = {"open": correct_time, "closed": None}

        # self.open_periods = new

    def add_images(self, images):
        self.images.append(images)

    def to_json(self):
        return {
            'id': self.id,
            'location': self.location,
            'name': self.name,
            'icon': self.icon,
            'close_to': self.vicinity,
            'url': self.url,
            'rating': self.rating,
            'number': self.local_phone_number,
            'website': self.website,
            'open_periods': self.open_periods
        }


# 31.894756, 34.809322
class query:
    def __init__(self, loc, radius, min_rating, place_type):
        self.lat, self.lng = loc
        # self.lat_lng = {'lat': self.lat, 'lng': self.lng}
        self.radius = radius
        self.rating_min = min_rating
        self.results = results([])
        self.type = place_type

    def get_all_pages(self, limit):
        query_results, next_k = find_places((self.lat, self.lng), self.radius, place_type=self.type, limit=limit)
        while next_k:
            data = find_places((self.lat, self.lng), self.radius, page_token=next_k)
            r, next_k = data
            if r:
                query_results += r

        for place in query_results:

            data_points = ["name", "icon", "place_id"]

            try:
                name = place["name"]
                icon = place["icon"]
                place_id = place['place_id']
            except TypeError:
                print("\n\n\n\n")
                print(place)
                print("\n\n\n\n")
                continue

            try:
                local_phone_number = place["formatted_phone_number"]
            except KeyError:
                local_phone_number = None

            try:
                close_to = place["vicinity"]
            except KeyError:
                close_to = None

            try:
                rating = place["rating"]
            except KeyError:
                rating = "None"

            try:
                website = place["website"]
            except KeyError:
                website = None

            try:
                url = place["url"]
            except KeyError:
                url = None

            try:
                open_now = place["opening_hours"]["open_now"]
                periods = place["opening_hours"]["weekday_text"]
            except:
                open_now = "opening_hours" not in place
                periods = None

            try:
                location = place["location"]["lat"], place["location"]["lng"]
            except:
                location = [0, 0]

            if open_now:
                try:
                    if rating > self.rating_min:
                        self.results.append(
                            Result_man(place_id, url, close_to, name, icon, rating, local_phone_number, website,
                                       periods, location))
                except:
                    self.results.append(
                        Result_man(place_id, url, close_to, name, icon,
                                   None, local_phone_number, website, periods, location))


def find_places(loc=(31.894756, 34.809322), radius=2_000, place_type="park", page_token=None, APIKEY=apikey, limit=-1):
    lat, lng = loc
    if page_token:
        url = f"https://maps.googleapis.com/maps/api/place/nearbysearch/json?" \
              f"pagetoken={page_token}" \
              f"&key={APIKEY}" \
              f"&language=en"
    else:
        url = f"https://maps.googleapis.com/maps/api/place/nearbysearch/json?" \
              f"&location={lat},{lng}" \
              f"&radius={radius}" \
              f"&type={place_type}" \
              f"&key={APIKEY}" \
              f"&language=en"

    response = get(url)
    res = json.loads(response.text)
    resses = []

    api_responds = res["results"][:limit]
    geometry = ["location"]
    for result in api_responds:
        info = {}
        for dat in ["name", "icon", "place_id", "opening_hours", "rating", "vicinity", "website", "location"]:
            try:
                if dat in geometry:
                    info[dat] = result["geometry"][dat]
                else:
                    info[dat] = result[dat]
            except KeyError:
                continue
        resses.append(info)
    # icon,place_id,name,opening_hours,rating,formatted_phone_number,vicinity,website,url


    # for p_id in ids:
    #     response = get(
    #         f"https://maps.googleapis.com/maps/api/place/details/json?place_id={p_id}&fields=icon,place_id,name,opening_hours,rating,formatted_phone_number,vicinity,website,url&key={apikey}")
    #     res = json.loads(response.text)
    #     try:
    #         resses.append(res["result"])
    #     except Exception as e:
    #         print(e)

    next_page_token = res.get("next_page_token", None)
    return resses, next_page_token


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
#
from datetime import datetime

gmaps = googlemaps.Client(key=apikey)


def get_name(lat, lng):
    gecoded = gmaps.reverse_geocode((lat, lng))
    print(gecoded)



def decode_polyline(polyline_str):
    index, lat, lng = 0, 0, 0
    coordinates = []
    changes = {'latitude': 0, 'longitude': 0}

    # Coordinates have variable length when encoded, so just keep
    # track of whether we've hit the end of the string. In each
    # while loop iteration, a single coordinate is decoded.
    while index < len(polyline_str):
        # Gather lat/lon changes, store them in a dictionary to apply them later
        for unit in ['latitude', 'longitude']:
            shift, result = 0, 0

            while True:
                byte = ord(polyline_str[index]) - 63
                index += 1
                result |= (byte & 0x1f) << shift
                shift += 5
                if not byte >= 0x20:
                    break

            if result & 1:
                changes[unit] = ~(result >> 1)
            else:
                changes[unit] = (result >> 1)

        lat += changes['latitude']
        lng += changes['longitude']

        coordinates.append((lat / 100000.0, lng / 100000.0))

    return coordinates


def draw_route(dest, waypoints, name, current_location=(31.894756, 34.809322)):
    # Request directions via public transit
    now = datetime.now()

    # locations = ["סטימצקי, Herzl Street, רחובות"]

    markers = ["color:blue|size:mid|label:" + chr(65 + i) + "|"
               + r for i, r in enumerate(waypoints)]
    # "כיכר המרכבה, Rehovot"
    # dest "קניון רחובות، Bilu Street, Rehovot"

    gmaps_results = gmaps.directions(origin=current_location,
                               destination=dest,
                               waypoints=waypoints,
                               departure_time=now)

    marker_points = []
    waypoints = []

    # extract the location points from the previous directions function

    for leg in gmaps_results[0]["legs"]:
        leg_start_loc = leg["start_location"]
        marker_points.append(f'{leg_start_loc["lat"]},{leg_start_loc["lng"]}')
        for step in leg["steps"]:
            end_loc = step["end_location"]
            waypoints.append(f'{end_loc["lat"]},{end_loc["lng"]}')
    last_stop = gmaps_results[0]["legs"][-1]["end_location"]
    marker_points.append(f'{last_stop["lat"]},{last_stop["lng"]}')

    markers = ["color:blue|size:mid|label:" + chr(65 + i) + "|"
               + r for i, r in enumerate(marker_points)]


    ma = str(markers[2:-2])
    # print(f"https://maps.googleapis.com/maps/api/staticmap?&center={waypoints[0]}&scale=2&zoom=13&size=640,640&format=jpg&maptype=roadmap&markers={ma}&path=" + "color:0x0000ff|weight:2|" + "|".join(waypoints))

    result_map = gmaps.static_map(
        center=waypoints[0],
        scale=10,
        zoom=15,
        size=[640, 640],
        format="jpg",
        maptype="roadmap",
        markers=markers,
        path="color:0x0000ff|weight:2|" + "|".join(waypoints))

    with open(f"static/{name}_route_map.jpg", "wb") as img:
        for chunk in result_map:
            img.write(chunk)

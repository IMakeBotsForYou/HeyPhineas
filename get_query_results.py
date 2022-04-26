import json

import googlemaps
from requests import get

from keys import *


class results:
    def __init__(self, r):
        self.results = r

    def get(self):

        data = {}

        for r in self.results:
            json_vr = r.to_json()
            data[json_vr["id"]] = json_vr

        return data

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

    def sort_by_distance(self):
        self.results.sort(key=lambda r: r.name)


class Place:
    def __init__(self, place_id, url, close_to, name, icon, rating, local_phone_number, website, open_periods,
                 location):
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

    def add_images(self, images):
        self.images.append(images)

    def to_json(self):
        return {
            'id': self.id,
            'location': list(self.location),
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
    def __init__(self, loc, radius, min_rating=0, place_type="park"):
        self.lat, self.lng = loc
        # self.lat_lng = {'lat': self.lat, 'lng': self.lng}
        self.radius = radius
        self.rating_min = min_rating
        self.results = results([])
        self.type = place_type

    def get_all_pages(self, limit=-1):
        query_results = find_places((self.lat, self.lng), self.radius, place_type=self.type, limit=limit)

        print("\n\n\n", query_results, "\n\n\n")
        for place in query_results:
            # data_points = ["name", "icon", "place_id"]
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
                periods = place["opening_hours"]["weekday_text"]
            except:
                periods = None

            try:
                location = place["location"]["lat"], place["location"]["lng"]
            except:
                location = [0, 0]

            # if open_now:
            if not rating:
                rating = 5
            try:
                if float(rating) > float(self.rating_min):
                    self.results.append(
                        Place(place_id, url, close_to, name, icon, rating, local_phone_number, website,
                              periods, location))
            except Exception as e:
                print(e)


def find_places(loc=(31.904052, 34.815355), radius=2_000, place_type="restaurant", limit=-1):
    lat, lng = loc
    # if page_token:
    #     url = f"https://maps.googleapis.com/maps/api/place/nearbysearch/json?" \
    #           f"pagetoken={page_token}" \
    #           f"&key={APIKEY}" \
    #           f"&language=en"
    # else:
    #     url = f"https://maps.googleapis.com/maps/api/place/nearbysearch/json?" \
    #           f"&location={lat},{lng}" \
    #           f"&radius={radius}" \
    #           f"&type={place_type}" \
    #           f"&key={APIKEY}" \
    #           f"&language=en"

    reverse_geocoded_data = json.loads(get(f"https://maps.googleapis.com/maps/api/geocode/json?latlng={lat},{lng}&key={apikey}").text)
    reverse_geocoded_city = reverse_geocoded_data["results"][0]["address_components"][2]["long_name"]

    req_fields = ["formatted_address", "name", "rating", "opening_hours", "geometry", "place_id"]
    req_comp = [f"input={place_type}s in {reverse_geocoded_city}", "inputtype=textquery",
                f"limit={limit}", f"fields={','.join(req_fields)}", f"key={apikey}",
                f"locationbias=circle:{radius}@{lat},{lng}"]

    req_url = f"https://maps.googleapis.com/maps/api/place/findplacefromtext/json?{'&'.join(req_comp)}"
    print(req_url)
    req_res = get(req_url)
    json_res = json.loads(req_res.text)
    final_results = []
    # print(req_url, json.dumps(json_res, indent=4))
    if limit != -1:
        api_responds = json_res["candidates"][:limit]
    else:
        api_responds = json_res["candidates"]
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
        final_results.append(info)
    # icon,place_id,name,opening_hours,rating,formatted_phone_number,vicinity,website,url

    # for p_id in ids:
    #     response = get(
    #         f"https://maps.googleapis.com/maps/api/place/details/json?place_id={p_id}&fields=icon,place_id,name,opening_hours,rating,formatted_phone_number,vicinity,website,url&key={apikey}")
    #     res = json.loads(response.text)
    #     try:
    #         resses.append(res["result"])
    #     except Exception as e:
    #         print(e)

    # next_page_token = json_res.get("next_page_token", None)
    return final_results


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #


gmaps = googlemaps.Client(key=apikey)


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

if __name__ == "__main__":
    print(find_places())

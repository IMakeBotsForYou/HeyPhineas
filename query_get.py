# from googleplaces import GooglePlaces, types, lang
# from keys import *
# import json
#
#
#
# class Result_man:
#     def __init__(self, place_id, close_to, place_types, name, icon, rating, local_phone_number, website, open_periods):
#         self.types = place_types
#         self.id = place_id
#         self.name = name
#         self.icon = icon
#         self.rating = rating
#         # self.rating_count = rating[1]
#         self.local_phone_number = local_phone_number
#         self.website = website
#         self.images = []
#         self.vicinity = close_to
#         self.open_periods = open_periods
#         print(self.to_json())
#
#     def add_images(self, images):
#         self.images.append(images)
#
#     def to_json(self):
#         return {
#             'id': self.id,
#             'name': self.name,
#             'icon': self.icon,
#             'close_to': self.vicinity,
#             'ratings': self.rating,
#             'types': self.types,
#             'number': self.local_phone_number,
#             'website': self.website,
#             'open_periods': self.open_periods
#         }
#
#
# # 31.894756, 34.809322
# class query:
#     def __init__(self, loc, radius, min_rating, place_type):
#         self.lat, self.lng = loc
#         # self.lat_lng = {'lat': self.lat, 'lng': self.lng}
#         self.radius = radius
#         self.rating_min = min_rating
#         self.results = []
#         self.type = place_type
#
#     def get_all_pages(self, limit):
#         query_results, next_k = find_places((self.lat, self.lng), self.radius, place_type=self.type)
#         while next_k:
#             data = find_places((self.lat, self.lng), self.radius, page_token=next_k)
#             r, next_k = data
#             if r:
#                 query_results += r
#
#         for place in query_results:
#             try:
#                 place_types = place["types"]
#                 name = place["name"]
#                 icon = place["icon"]
#                 place_id = place['place_id']
#             except TypeError:
#                 print("\n\n\n\n")
#                 print(place)
#                 print("\n\n\n\n")
#                 continue
#
#             try:
#                 local_phone_number = place["formatted_phone_number"]
#             except KeyError:
#                 local_phone_number = None
#
#             try:
#                 close_to = place["vicinity"]
#             except KeyError:
#                 close_to = None
#
#             try:
#                 rating = place["rating"]
#             except KeyError:
#                 rating = "None"
#
#             try:
#                 website = place["website"]
#             except KeyError:
#                 website = None
#
#             try:
#                 open_now = place["opening_hours"]["open_now"]
#                 periods = place["opening_hours"]["periods"]
#             except:
#                 open_now = "opening_hours" not in place
#                 periods = None
#
#             if open_now and len(self.results) < limit:
#                 try:
#                     if rating > self.rating_min:
#                         self.results.append(
#                             Result_man(place_id, close_to, place_types, name, icon, rating, local_phone_number, website, periods))
#                 except:
#                     self.results.append(
#                         Result_man(place_id, close_to, place_types, name, icon, None, local_phone_number, website, periods))
#

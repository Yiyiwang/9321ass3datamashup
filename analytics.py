from collections import defaultdict

debug_print = False


class RestaurantAnalytics:
    """
    Provides methods to analyse the list of restaurants and their locations.
    """

    @staticmethod
    def top_restaurant_types(restaurant_list):
        """
        Calculates the most favourable types of restaurants in the
        geo-location provided.
        """
        # get the list of restaurants
        restaurants = restaurant_list['restaurants']
        restaurant_types = defaultdict(int)
        # go through each restaurant in the list and add the occurrences of the types present
        for restaurant in restaurants:
            for source in restaurant['sources']:
                for type in source['types']:
                    if type not in establishment_types:
                        #restaurant_types[type + '-' + source['source name']] += 1
                        restaurant_types[type] += 1

        # reverse dict and sort by occurrence
        sorted_restaurant_types = sorted(
            restaurant_types.items(), key=lambda i: i[1], reverse=True
        )

        if debug_print:
            print(restaurants)
            print(sorted_restaurant_types)
        return sorted_restaurant_types[0]


establishment_types = [
    'establishment', 'food', 'lodging', 'night_club', 'point_of_interest'
    , 'restaurant'
]

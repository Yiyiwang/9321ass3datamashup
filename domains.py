import json


class SourceMetadata:
    def __init__(self, source_id, rating, votes, type, url):
        self.source_id = source_id
        self.rating = int(rating)
        self.votes = int(votes)
        self.type = type
        self.url = url
        super().__init__()

    def toJSON(self):
        return dict(source_id=self.source_id, rating=self.rating
                    , votes=self.votes, type=self.type, url=self.url)


class Restaurant:
    def __init__(self, name, address, source_id, rating, votes, type, url, zomato=False, google=False):
        self.name = name
        self.address = address
        self.zomato = None
        self.google = None
        if zomato is True:
            self.zomato = self._add_source_metadata(source_id, rating, votes, type, url)
        if google is True:
            self.google = self._add_source_metadata(source_id, rating, votes, type, url)
        self.aggregate_rating = self._aggregate_rating()
        super().__init__()

    def _add_source_metadata(self, source_id, rating, votes, type, url):
        return SourceMetadata(source_id, rating, votes, type, url)

    def _aggregate_rating(self):
        z_rating = 0
        z_votes = 0
        g_rating = 0
        g_votes = 0
        if self.zomato is not None:
            z_rating = self.zomato.rating
            z_votes = self.zomato.votes
        if self.google is not None:
            g_rating = self.google.rating
            g_votes = self.google.votes
        return (
            (z_rating * z_votes + g_rating * g_votes) /
            (z_votes + g_votes)
        )

    def toJSON(self):
        # using json.dumps with encoder for final object to json output
        return json.dumps(
            dict(name=self.name, address=self.address, zomato=self.zomato
                 , google=self.google, aggregate_rating=self.aggregate_rating)
            , cls=ComplexEncoder
        )


# Encoder for complex python objects
class ComplexEncoder(json.JSONEncoder):
    def default(self, o):
        if hasattr(o, "toJSON"):
            return o.toJSON()
        else:
            return json.JSONEncoder.default(self, o)

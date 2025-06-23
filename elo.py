


class EloRating:
    def __init__(self, k=20, base_rating=1500):
        self.k = k
        self.ratings = {}
        self.base_rating = base_rating

    def get_rating(self, team):
        return self.ratings.get(team, self.base_rating)

    def expected_result(self, rating1, rating2):
        return 1 / (1 + 10 ** ((rating2 - rating1) / 400))

    def update_ratings(self, team1, team2, result):
        r1 = self.get_rating(team1)
        r2 = self.get_rating(team2)

        expected1 = self.expected_result(r1, r2)
        expected2 = self.expected_result(r2, r1)

        self.ratings[team1] = r1 + self.k * (result - expected1)
        self.ratings[team2] = r2 + self.k * ((1 - result) - expected2)

    def get_all_ratings(self):
        return dict(sorted(self.ratings.items(), key=lambda item: item[1], reverse=True))

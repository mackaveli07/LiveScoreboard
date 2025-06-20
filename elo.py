
# elo.py

class EloRating:
    def __init__(self, initial_rating=1500, k=20):
        self.ratings = {}
        self.k = k
        self.initial_rating = initial_rating

    def get_rating(self, team):
        return self.ratings.get(team, self.initial_rating)

    def expected_score(self, rating_a, rating_b):
        return 1 / (1 + 10 ** ((rating_b - rating_a) / 400))

    def update_ratings(self, team_a, team_b, result):
        rating_a = self.get_rating(team_a)
        rating_b = self.get_rating(team_b)

        expected_a = self.expected_score(rating_a, rating_b)
        expected_b = self.expected_score(rating_b, rating_a)

        self.ratings[team_a] = rating_a + self.k * (result - expected_a)
        self.ratings[team_b] = rating_b + self.k * ((1 - result) - expected_b)

    def get_all_ratings(self):
        return dict(sorted(self.ratings.items(), key=lambda x: -x[1]))

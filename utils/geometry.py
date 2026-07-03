import math


class Geometry:

    @staticmethod
    def euclidean(p1, p2):

        return math.sqrt(

            (p1.x - p2.x) ** 2 +

            (p1.y - p2.y) ** 2
        )
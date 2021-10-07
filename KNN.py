import numpy as np


class KNN:
    def __init__(self, vls=None, k: int = 0):

        if vls is None:
            vls = {}
        '''
        ### The values parameter should look like this:
                {
                    label: (x, y, z...), 
                    label2: (x, y, z...),
                    ...
                }
        '''
        self.values: dict = vls
        self.labels = [value[0] for value in self.values]
        self.distances: np.array[tuple[any, float]] = np.array([])
        self.k: int = k
        self.origin = None

    def set_origin(self, origin):
        if origin in self.values:
            self.origin = self.values[origin]
        else:
            self.origin = origin

    def set_values(self, vls):
        self.values = vls

    def _euclidean_dist(self, target_point: np.array) -> float:
        return np.linalg.norm(self.origin - target_point)

    def run(self, n=None, weigh_values=None):
        """
        :param weigh_values: user-controlled function to weigh the
        :param n: Number of nearest neighbours to return
        :return: K-NN labels
        """
        assert self.origin is not None
        distances = []

        for label in self.values:
            dist = self._euclidean_dist(self.values[label])
            weight = 1
            if weigh_values:
                weight = weigh_values(label, dist)
                weight = 1 if weight == 0 else weight

            distances.append((label, dist / weight))

        distances.sort(key=lambda info: info[1])
        if n is None:
            n = int(np.sqrt(len(self.values)))
        return distances[:n]
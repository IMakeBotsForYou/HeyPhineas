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
        self.labels = list(self.values.keys())
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
        return np.linalg.norm(self.origin - np.array(target_point))

    def run(self, n=None, weigh_values=None):
        """
        :param weigh_values: user-controlled function to weigh the
        :param n: Number of nearest neighbours to return
        :return: K-NN labels
        """
        assert self.origin is not None
        labels = list(self.values.keys())
        vectors = list(self.values.values())
        if weigh_values is None:
            distances = [self._euclidean_dist(np.array(vector)) for vector in vectors]
        else:
            distances = [weigh_values(label, self._euclidean_dist(np.array(vector)))
                         for label, vector in zip(labels, vectors)]

        labeled_distances = [(label, dist) for label, dist in zip(labels, distances)]

        labeled_distances.sort(key=lambda info: info[1])
        if n is None and self.k == 0:
            n = int(np.sqrt(len(self.values)))
        else:
            n = self.k
        return labeled_distances[1:n]


if __name__ == "__main__":
    values = {
        "Dan": [5, 5, 5],
        "Rudich": [4, 4, 4],
        "Guy": [4.5, 4, 3],
        "Bruh": [1, 5, 5]
    }
    import random
    # for a in range(10000):
    #     values[str(a)] = [random.random()*5]*3
    print("Done")
    knn = KNN(values, 3)
    knn.set_origin("Dan")
    print(knn.run())
    knn.run()


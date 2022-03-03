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
        self.distances = np.array([])
        self.k: int = k
        self.origin = None
        self.groups: dict

    def set_origin(self, name):
        self.origin = name

    def set_values(self, vls):
        self.values = vls

    def _euclidean_dist(self, target_point: np.array) -> float:

        return np.linalg.norm(np.array(self.values[self.origin]) - np.array(target_point))

    def get_closest(self, n=None, weigh_values=None, only_these_values=None, names_only=False):
        """
        :param only_these_values: only run on certain values
        :param weigh_values: user-controlled function to weigh the
        :param n: Number of nearest neighbours to return
        :return: K-NN labels
        """
        assert self.origin is not None
        saved_values = None
        if only_these_values is not None:
            saved_values = self.values
            self.values = only_these_values

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
        final_values = labeled_distances[1:n]

        if only_these_values is not None:
            self.values = saved_values

        if names_only:
            return [x[0] for x in final_values]

        return final_values


if __name__ == "__main__":
    values = {
        "Dan": [5, 5],
        "Rudich": [4, 4],
        "Guy": [4.5, 4],
        "Shoshani": [4, 5],

        "Fefer": [1, 2],
        "Maya": [2, 3],
        "Yasha": [1, 1],
    }
    import random

    # for a in range(100):
    #     values[str(a)] = [random.random() * 5] * 2

    knn = KNN(values, 3)
    knn.set_origin("Dan")
    flag = True
    closest = {}
    middles = {}
    for name in values:
        knn.set_origin(name)
        closest[knn.origin] = {"closest": knn.get_closest(names_only=True), "in group": False}

    for name in values:
        middle_x, middle_y = sum(coord[0] for coord in closest[name]["closest"]) / 3, \
                             sum(coord[1] for coord in closest[name]["closest"]) / 3
        middle = middle_x, middle_y
        knn.set_origin(middle)
        knn.get_closest()














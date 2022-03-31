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

    def group_clusters(self, centroids):
        centroids = dict.fromkeys(centroids, [])
        for vec in self.values.values():
            min_dist, best_centroid = 10**99, None
            for center in centroids:
                dist = np.linalg.norm(np.array(center) - np.array(vec))
                if dist < min_dist:
                    min_dist = dist
                    best_centroid = center
            centroids[best_centroid] = best_centroid
        return centroids

    def set_origin(self, name):
        self.origin = name

    def set_values(self, vls):
        self.values = vls

    def _euclidean_dist(self, target_point: np.array) -> float:
        if self.origin in self.values:
            return np.linalg.norm(np.array(self.values[self.origin]) - np.array(target_point))
        else:
            return np.linalg.norm(np.array(self.origin) - np.array(target_point))

    def get_closest(self, n=None, weigh_values=None, only_these_values=None,
                    names_only=False, verbose=False, remove_first=True):
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
        if verbose:
            print(self.origin, [x[0] for x in labeled_distances])
        save_k = self.k
        if n is None and self.k == 0:
            n = int(np.sqrt(len(self.values)))
        elif n is None:
            n = self.k
            # self.k = n
        else:
            self.k = n
            # n = self.k

        final_values = labeled_distances[1:n] if remove_first else labeled_distances[:n]

        if only_these_values is not None:
            self.values = saved_values

        if names_only:
            return [x[0] for x in final_values]

        self.k = save_k
        return final_values


def get_intersection(a, b):
    return list(set(a) & set(b))


if __name__ == "__main__":
    values = {
        "Dan": [5, 5],
        "Rudich": [4, 4],
        "Guy": [4.5, 4],
        "Shoshani": [4, 5],

        "Fefer": [1, 2],
        "Maya": [2, 2],
        "Yasha": [1, 1],

        "Eran": [3, 3]
    }

    import random

    # for a in range(100):
    #     values[str(a)] = [random.random() * 5] * 2

    knn = KNN(values, k=4)
    knn.set_origin("Dan")
    flag = True



    i = 0

    centroids_amount = 2
    centroids = {[random.uniform(1, 5)] * centroids_amount}

    centroids = knn.group_clusters(centroids)









    # for name in values:
    #     if name in included:
    #         continue
    #     # print(name + f"\t{closest[name]['closest']}")
    #     new_list = {value: knn.values[value] for value in knn.values if not closest[value]["in group"]}
    #     middle_x, middle_y = sum([knn.values[user][0] for user in closest[name]["closest"] if user in new_list]) \
    #                          / len(closest[name]['closest']), \
    #                          sum([knn.values[user][1] for user in closest[name]["closest"] if user in new_list]) \
    #                          / len(closest[name]['closest'])
    #     middle = middle_x, middle_y
    #     knn.set_origin(middle)
    #     a = knn.get_closest(only_these_values=new_list,
    #                         names_only=True, n=4, verbose=False, remove_first=False)
    #     for user in a:
    #         closest[user]["in group"] = True
    #     print(f"GROUP {i}: {a}")
    #     included += a
    #     included = list(set(included))
    #     # print(included)
    #     i += 1

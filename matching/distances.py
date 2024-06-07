import numpy as np
from scipy.spatial.distance import euclidean, mahalanobis
from dtw import dtw

class Distances_method:
    def euclidean(person1_pos, person2_pos):
        distance = euclidean(person1_pos, person2_pos)
        return distance
    
    def corrected_euclidean(person1_pos, person2_pos, person1_ratio, person2_ratio):
        distance = euclidean(person1_pos, person2_pos)
        distance = distance * ((person1_ratio + person2_ratio) / 2)
        return distance
    
    def correlation(person1_pos, person2_pos):
        correlation = np.corrcoef(person1_pos, person2_pos)[0, 1]
        return correlation
    
    def frechet(person1_tracklet, person2_tracklet):
        n = len(person1_tracklet)
        m = len(person2_tracklet)
        D = np.zeros((n, m))
        for i in range(n):
            for j in range(m):
                D[i, j] = ((person1_tracklet[i][1]-person2_tracklet[j][1])**2 + (person1_tracklet[i][2]-person2_tracklet[j][2])**2 + (person1_tracklet[i][0]-person2_tracklet[j][0])**2)**(1/2)
        C = np.zeros((n + 1, m + 1))
        for i in range(n + 1):
            for j in range(m + 1):
                C[i, j] = np.inf
        C[0, 0] = 0
        for i in range(1, n + 1):
            for j in range(1, m + 1):
                C[i, j] = min(C[i - 1, j], C[i, j - 1], C[i - 1, j - 1]) + D[i - 1, j - 1]
        return C[n, m]
    
    def mahalanobis(person1_tracklet, person1_pos, person2_pos):
        # Find the covariance matrix
        cov = np.cov(person1_tracklet, rowvar=False)
        # Find the inverse matrix
        inv_cov = np.linalg.inv(cov)
        distance = mahalanobis(person1_pos, person2_pos, inv_cov)
        return distance
    
    def dtw(person1_tracklet, person2_tracklet):
        dist, cost, acc, path = dtw(person1_tracklet, person2_tracklet, dist=lambda x, y: np.linalg.norm(x - y))
        return dist


import torch
import numpy as np
import sys
from torch.nn import functional as F

def extract_gallery_feature(gallery_list):
    gallery_id = []
    gallery_feature = torch.FloatTensor()
    for gallery in gallery_list:
        gallery_id.append(gallery[1])
        gallery_feature = torch.cat((gallery_feature, gallery[0]), 0)
    return gallery_feature, gallery_id
    
def extract_query_feature(query):
    query_feature, query_id, query_frame, query_dir = query
    return query_feature, query_id, query_frame, query_dir
    
def score(gallery_feature, query_feature):
    gallery_feature = torch.from_numpy(gallery_feature).clone()
    query_feature = torch.from_numpy(query_feature).clone()
    gallery_feature = gallery_feature.unsqueeze(0)  
    query_feature = query_feature.unsqueeze(0)    
    gallery_feature = F.normalize(gallery_feature, p=2, dim=1)
    query_feature = F.normalize(query_feature, p=2, dim=1)
    score = torch.mm(gallery_feature, query_feature.t())
    score = score.squeeze(1).cpu()
    #index = np.argsort(-score)  # from small to large
    return score
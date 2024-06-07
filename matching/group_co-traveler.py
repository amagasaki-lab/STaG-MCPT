import os
import pandas as pd
import numpy as np
import argparse
from tqdm import tqdm
import time
import math
import extract_feature
import utility
import filtering

def make_parser():
    parser = argparse.ArgumentParser("Start Co-traveler!")
    parser.add_argument("--query_txt_path", default='output/grouping/', help="input query group tracking path")
    parser.add_argument("--gallery_txt_path", default='output/grouping/', help="input gallery group tracking path")
    parser.add_argument("--query_list", default='output/features/', help="input query features npy")
    parser.add_argument("--gallery_list", default='output/features/', help="input gallery features npy")
    parser.add_argument("--query_cam", default='cameraA', choices=["cameraA", "cameraB", "cameraC"], help="input query camera")
    parser.add_argument("--gallery_cam", default='cameraB', choices=["cameraA", "cameraB", "cameraC"], help="input gallery camera")
    parser.add_argument("--save_path", default='output/result/', help="input save path")
    parser.add_argument("--alpha", default=0.9, help="input an alpha value")
    parser.add_argument("--beta", default=1, help="input a beta value")
    return parser

def extract_group_info(df, df1):
    groups = []
    group_frame = []
    group_number = []
    group_dir = []
    group_label = [] #0 for a single person, 1 for a group (2 or more) formed
    for i in df["group_id"].unique():
        group_number.append(i)
    group_number = sorted(group_number)

    for i in group_number:
        df_group = df[df['group_id'] == i]
        df_drop_id = df_group.drop_duplicates("Id") 
        list_group = df_drop_id['Id'].to_list()
                
        if i == 0: # For one person
            for z in list_group:
                filtered_df = df1[df1[1].isin([z])] 
                min_value = filtered_df[2].min() 
                if not math.isnan(min_value):
                    groups.append([z, z])
                    group_label.append(0)
                    group_frame.append(int(min_value))
                    group_dir.append(filtered_df[3].mode()[0]) 
            
        else: # For groups (of two or more people)
            filtered_df = df1[df1[1].isin(list_group)]
            min_value = filtered_df[2].min()
            #if math.isnan(min_value):
            #    continue
            groups.append(list_group) 
            group_label.append(1) 
            group_frame.append(int(min_value))
            group_dir.append(filtered_df[3].mode()[0])

    return groups, group_frame, group_label, group_dir

# CTS
class CoTraveler:
    def __init__(self, query_cam, gallery_cam, query_list, gallery_list, query_groups, query_group_frame, query_group_dir, query_group_label, gallery_groups, gallery_group_frame, gallery_group_dir, gallery_group_label):
        self.query_cam = query_cam
        self.query_list = query_list
        self.query_groups = query_groups
        self.query_group_frame = query_group_frame
        self.query_group_dir = query_group_dir
        self.query_group_label = query_group_label
        self.gallery_cam = gallery_cam
        self.gallery_list = gallery_list
        self.gallery_groups = gallery_groups
        self.gallery_group_frame = gallery_group_frame
        self.gallery_group_dir = gallery_group_dir
        self.gallery_group_label = gallery_group_label
        self.all_output = [] 
    
    # Group-aware ID matching
    def pair_match(self, query_id, query_feature, filtering_result, alpha, beta):
        indices = [row for row, item in enumerate(self.query_groups) if query_id in item][0] 
        query_group = self.query_groups[indices]
        C_query = query_group[:]
        C_query.remove(query_id) 
        query_label = self.query_group_label[indices]
        Pi_query_feature = query_feature
        if all(element == False for element in filtering_result): # If no matching with any gallery ID due to spatio-temporal filtering
            self.all_output.append([query_id, 'NONE'])     
        else:
            distances_group = self._calculate_distances(query_id, query_label, Pi_query_feature, filtering_result, alpha, C_query)
            normalized_list = self._normalize_list(distances_group)
            self._compute_final_distances(query_id, query_label, Pi_query_feature, filtering_result, beta, normalized_list)
        
        return self.all_output

    # Group-aware similarity calculation between a single query ID and gallery groups
    def _calculate_distances(self, query_id, query_label, Pi_query_feature, filtering_result, alpha, C_query):
        distances_group = []
        for i, filter in enumerate(filtering_result): 
            if filter:
                if self.gallery_group_label[i] == 0: 
                    gallery_groups = [self.gallery_groups[i][0]] 
                else:
                    gallery_groups = self.gallery_groups[i]
                distances = self._calculate_distances_Pi_Pj(query_id, query_label, Pi_query_feature, i, gallery_groups, alpha, C_query) 
                distances_group.extend(distances) 
        return distances_group

    # Group-aware similarity calculation between a single query ID and a single gallery group
    def _calculate_distances_Pi_Pj(self, query_id, query_label, Pi_query_feature, gallery_idx, gallery_groups, alpha, C_query):
        distances_in_group = []
        for x, Pj_gallery_id in enumerate(gallery_groups): 
            Pj_gallery_feature = self._get_gallery_feature(Pj_gallery_id)
            score_Pi_Pj = extract_feature.score(Pj_gallery_feature, Pi_query_feature)  
            C_gallery = gallery_groups[:x] + gallery_groups[x+1:] # Extract the gallery IDs of interest
            distances = self._calculate_distances_in_group(Pi_query_feature, Pj_gallery_feature, C_gallery, query_id, query_label, alpha, score_Pi_Pj, C_query, gallery_idx)
            distances_in_group.extend(max(distances))
        return distances_in_group

    # Group-aware similarity calculation between a single query ID and a single gallery ID
    def _calculate_distances_in_group(self, Pi_query_feature, Pj_gallery_feature, C_gallery, query_id, query_label, alpha, score_Pi_Pj, C_query, gallery_idx):
        distances = []
        for Pm_query_id in C_query: 
            Pm_query_feature = self._get_query_feature(Pm_query_id)
            if self.gallery_group_label[gallery_idx] == 0: 
                C_gallery = []
                score_Pm_Pn = extract_feature.score(Pj_gallery_feature, Pm_query_feature) 
                d_Pim_query_and_Pjn_gallery = alpha * score_Pi_Pj + (1 - alpha) * score_Pm_Pn
                distances.append(d_Pim_query_and_Pjn_gallery)
            for Pn_gallery_id in C_gallery: 
                Pn_gallery_feature = self._get_gallery_feature(Pn_gallery_id)
                score_Pm_Pn = extract_feature.score(Pn_gallery_feature, Pm_query_feature)
                d_Pim_query_and_Pjn_gallery = alpha * score_Pi_Pj + (1 - alpha) * score_Pm_Pn
                distances.append(d_Pim_query_and_Pjn_gallery)
        return distances
    
    # Get the features of the gallery ID
    def _get_gallery_feature(self, gallery_id):
        return [row[0] for row in self.gallery_list if row[1] == gallery_id][0]
    
    # Get the features of the query ID.
    def _get_query_feature(self, query_id):
        return [row[0] for row in self.query_list if row[1] == query_id][0]
    
    # Min_max normalization
    def _normalize_list(self, distances_group):
        min_value = min(distances_group)
        max_value = max(distances_group)
        normalized = [(x - min_value) / (max_value - min_value) * 0.9 + 0.1 for x in distances_group]
        return normalized
    
    # Calculate final similarity
    def _compute_final_distances(self, query_id, query_label, Pi_query_feature, filtering_result, beta, normalized_list):
        z = 0
        final_result = []

        for i, filter in enumerate(filtering_result): 
            if filter:
                if self.gallery_group_label[i] == 0: 
                    gallery_groups = [self.gallery_groups[i][0]]
                else:
                    gallery_groups = self.gallery_groups[i]
                z, final_distances = self._compute_final_individual_scores(query_id, query_label, Pi_query_feature, i, gallery_groups, beta, normalized_list, z)
                final_result.extend(final_distances)
        sorted_final_results = sorted(final_result, key=lambda x: x[1], reverse=True) 
        self._append_to_final_distances(query_id, sorted_final_results)
    
    # Calculate final similarity between a single query ID and a single gallery ID
    def _compute_final_individual_scores(self, query_id, query_label, Pi_query_feature, gallery_idx, gallery_groups, beta, normalized_list, z):
        final_distances = []
        for gallery_id in gallery_groups:
            Pj_gallery_feature = self._get_gallery_feature(gallery_id)
            score_Pi_Pj = extract_feature.score(Pj_gallery_feature, Pi_query_feature) 
            if query_label == self.gallery_group_label[gallery_idx]: 
                beta1 = 1
            else:
                beta1 = beta
            final_score = beta1 * normalized_list[z] * score_Pi_Pj
            final_distances.append([gallery_id, final_score]) 
            z += 1
        return z, final_distances
    
    # Store the query ID and corresponding gallery ID from rank-1 to rank-3
    def _append_to_final_distances(self, query_id, sorted_final_results):
        if len(sorted_final_results) == 1:
            self.all_output.append([query_id, sorted_final_results[0][0], None, None])
        elif len(sorted_final_results) == 2:
            self.all_output.append([query_id, sorted_final_results[0][0], sorted_final_results[1][0], None])
        else:
            self.all_output.append([query_id, sorted_final_results[0][0], sorted_final_results[1][0], sorted_final_results[2][0]])
    
    

def main(args):
    a = os.path.join(args.query_list, f"{args.query_cam}.npy")
    labels = ["Frame","Id", "group_id", "x","y","w","h","conf","a1","a2","a3"]
    query_group_info = pd.read_csv(os.path.join(args.query_txt_path, f"{args.query_cam}.txt"), names=labels)
    gallery_group_info = pd.read_csv(os.path.join(args.gallery_txt_path, f"{args.gallery_cam}.txt"), names=labels)
    query_list = np.load(os.path.join(args.query_list, f"{args.query_cam}_feature.npy"), allow_pickle=True)
    gallery_list= np.load(os.path.join(args.gallery_list, f"{args.gallery_cam}_feature.npy"), allow_pickle=True) #[feature, id, frame, direction]
    df_query = pd.DataFrame(query_list)
    df_gallery = pd.DataFrame(gallery_list)

    query_groups, query_group_frame, query_group_label, query_group_dir = extract_group_info(query_group_info, df_query)
    gallery_groups, gallery_group_frame, gallery_group_label, gallery_group_dir = extract_group_info(gallery_group_info, df_gallery)
    co_traveler = CoTraveler(args.query_cam, args.gallery_cam, query_list, gallery_list, query_groups, query_group_frame, query_group_dir, query_group_label, gallery_groups, gallery_group_frame, gallery_group_dir, gallery_group_label)
    filter = filtering.Filtering(args.query_cam, args.gallery_cam, query_group_frame, query_group_dir, query_groups, gallery_group_frame, gallery_group_dir)
    
    for query in tqdm(query_list):
        query_feature, query_id, query_frame, query_dir = extract_feature.extract_query_feature(query)
        min_frame, max_frame = filter.filtering_info(query_dir)
        filtering_result =  filter.filtering_group_process(query_id, min_frame, max_frame) # Spatio-temporal filtering
        all_output = co_traveler.pair_match(query_id, query_feature, filtering_result, args.alpha, args.beta)
    
    save_path = f"{args.save_path}/q{args.query_cam}_g{args.gallery_cam}.xlsx"
    utility.convert_excel(save_path, all_output)

if __name__ == '__main__':
    args = make_parser().parse_args()
    main(args)
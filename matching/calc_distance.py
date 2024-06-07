import argparse
from distances import Distances_method
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import os

def make_parser():
    parser = argparse.ArgumentParser("Calculate distance!")
    parser.add_argument("--input_file", default='data/single_camera_tracking/', help="Input file directory")
    parser.add_argument("--cam", default='cameraA', choices=["cameraA", "cameraB", "cameraC"], help="Enter name of camera")
    parser.add_argument("--distance_method", default='corrected_euclidean', choices=['euclidean' or 'corrected_euclidean' or 'correlation' or 'frechet' or 'mahalanobis' or 'dtw'], help="Enter the distance calculation method")
    parser.add_argument("--xy", default='x1', choices=['x1', 'y2'],help="When correlating, do we use x or y?")
    parser.add_argument('--save_fig', action='store_true', help="Whether to save the figure or not")
    parser.add_argument('--save_fig_path', default='output/figure/', help="Enter the path where you want to save the figure")
    parser.add_argument("--output_file", default='output/distances/', help="output file")
    return parser

# Select an ID that matches the criteria
def search_id(df, id):
    condition = df["Id"] == id
    selected_col = df[condition]
    return selected_col

# List specified columns
def col_to_list(df, col):
    col_list = df['{}'.format(col)].tolist()
    return col_list

# Find an angle
def calc_angle(start_position, end_position, cam = 'cameraA'):
    vec = end_position - start_position
    angle = np.rad2deg(np.arctan2(vec[0], vec[1]))
    if cam == 'cameraB':
        if (angle < -90) or (angle > 90):
            dir = 1
        else:
            dir = 2
    
    elif cam == 'cameraA':
        if (angle < 45) and (angle > -135):
            dir = 1
        else:
            dir = 2
    
    elif cam == 'cameraC':
        if angle > 0:
            dir = 1
        else:
            dir = 2   
    return dir

# Creating a polyline diagram
def make_fig(times, distances, query_h_list, gallery_h_list, path, z):
    plt.plot(times, distances, label = 'distance')
    plt.plot(times, query_h_list, label = 'query_height')
    plt.plot(times, gallery_h_list, label = 'gallery_height')
    plt.legend()
    os.makedirs(path, exist_ok=True)
    plt.savefig(f'{path}/gallery_{z}.png')
    plt.clf()

def main(args):
    output_query_id = []
    output_gallery_id = []
    output_distances = []
    average_distances = []
    max_distances = []
    min_distances = []
    var_distances = []
    
    input_file = os.path.join(args.input_file, f"{args.cam}.txt")
    labels = ["Frame","Id","x1","y1","x2","y2","conf","a1","a2","a3"]
    df = pd.read_csv(input_file, names=labels)

    # <bb_left>,<bb_top>,<bb_width>,<bb_height> are stored in this order
    df['y1'] = df['y1'] + df['y2']

    # Calculate the distance
    for count, i in enumerate(df["Id"].unique()):
        print(f'{count+1} / {len(df["Id"].unique())}')

        query_info = search_id(df, i)
        query_time_list = col_to_list(query_info, 'Frame')
        if max(query_time_list)-min(query_time_list) < 30:
            continue
        query_x_list = col_to_list(query_info, 'x1')
        query_y_list = col_to_list(query_info, 'y1')
        query_h_list = col_to_list(query_info, 'y2') 

        data1 = {'time': query_time_list, 'x': query_x_list, 'y': query_y_list, 'h': query_h_list} ##
        df1 = pd.DataFrame(data1)
        df1_query = df1[['time', 'x', 'y']]
        query_tracklet = df1_query.to_numpy()
        query_start_position = np.array([query_tracklet[0, 1], query_tracklet[0, 2]])
        query_end_position = np.array([query_tracklet[-1, 1], query_tracklet[-1, 2]])
        query_dir = calc_angle(query_start_position, query_end_position, args.cam)
        
        for z in df["Id"].unique():
            if i >= z:
                continue
            gallery_info = search_id(df, z)
            if not any(gallery_info['Frame'].isin(query_time_list)):
                continue
            if gallery_info['Frame'].isin(query_time_list).sum() < 30:
                continue
            gallery_time_list = col_to_list(gallery_info, 'Frame')
            if max(gallery_time_list)-min(gallery_time_list) < 30:
                continue

            gallery_x_list = col_to_list(gallery_info, 'x1')
            gallery_y_list = col_to_list(gallery_info, 'y1')
            gallery_h_list = col_to_list(gallery_info, 'y2')

            data2 = {'time': gallery_time_list, 'x': gallery_x_list, 'y': gallery_y_list, 'h': gallery_h_list} 
            df2 = pd.DataFrame(data2)
            df2_gallery = df2[['time', 'x', 'y']]
            gallery_tracklet = df2_gallery.to_numpy()
            gallery_start_position = np.array([gallery_tracklet[0, 1], gallery_tracklet[0, 2]])
            gallery_end_position = np.array([gallery_tracklet[-1, 1], gallery_tracklet[-1, 2]])
            gallery_dir = calc_angle(gallery_start_position, gallery_end_position, args.cam)
    
            if not (query_dir == gallery_dir):
                continue

            if args.distance_method == 'frechet':
                frechet_distance = Distances_method.frechet(query_tracklet, gallery_tracklet)
                output_query_id.append(i)
                output_gallery_id.append(z)
                output_distances.append(frechet_distance)
                continue

            if args.distance_method == 'dtw':
                print(i, z)
                query_tracklet2 = np.delete(query_tracklet, 0, axis=1)
                gallery_tracklet2 = np.delete(gallery_tracklet, 0, axis=1)
                dtw_distance = Distances_method.dtw(query_tracklet2, gallery_tracklet2)
                output_query_id.append(i)
                output_gallery_id.append(z)
                output_distances.append(dtw_distance)
                continue

            distances = []
            times = [] 
            query_h_list = []
            gallery_h_list = []
            query_xy = []
            gallery_xy = []

            for w in range(len(df1)):
                target = int(df1.time[w])
                if df2[df2["time"].eq(target)].empty:
                    continue
                else:
                    df3 = df2['time'] == df1.time[w]
                    df3 = df2[df3]
                    if args.distance_method == 'mahalanobis':
                        mahalanobis_tracklet = df1[['x', 'y']]
                        X = [df1.x[w], df1.y[w]]
                        Y = [df3.iloc[0,1], df3.iloc[0,2]]
                        mahalanobis_distance = Distances_method.mahalanobis(mahalanobis_tracklet, X, Y)
                        distances.append(mahalanobis_distance)
                        continue
                    
                    times.append(target)
                    distance = Distances_method.euclidean([df1.x[w], df1.y[w]],[df3.iloc[0,1], df3.iloc[0,2]])
                    query_h_list.append(df1.h[w])
                    gallery_h_list.append(df3.iloc[0,3])
                    query_ratio = 80 / df1.h[w]
                    gallery_ratio = 80 / df3.iloc[0,3]

                    if args.distance_method == 'euclidean':
                        query_ratio = df1.h[w] / 170
                        gallery_ratio = df3.iloc[0,3] / 170
                        distance = distance / ((query_ratio + gallery_ratio) / 2)
                        distances.append(distance)
                        continue

                    if args.distance_method == 'corrected_euclidean':
                        distance = distance * ((query_ratio + gallery_ratio) / 2)
                        distances.append(distance)
                        continue
                    
                    if args.distance_method == 'correlation':
                        if args.xy == 'x1':
                            query_xy.append(df1.x[w])
                            gallery_xy.append(df3.iloc[0,1])
                        else:
                            query_xy.append(df1.y[w])
                            gallery_xy.append(df3.iloc[0,2])
            
            if args.distance_method == 'correlation':
                distance = np.corrcoef(query_xy, gallery_xy)[0, 1]
                output_query_id.append(i)
                output_gallery_id.append(z)
                output_distances.append(distance)
        
            if args.save_fig:
                print('a')
                save_fig_path = os.path.join(args.save_fig_path, f"{args.cam}/")
                if not os.path.exists(save_fig_path):
                    os.makedirs(save_fig_path)
                make_fig(times, distances, query_h_list, gallery_h_list, f'{save_fig_path}/query_{i}', z)
            
            if args.distance_method == 'euclidean' or args.distance_method == 'corrected_euclidean' or args.distance_method == 'mahalanobis':
                output_query_id.append(i)
                output_gallery_id.append(z)
                average_distance = sum(distances)/len(distances)
                max_distance = max(distances)
                min_distance = min(distances)
                var = np.var(distances)
                average_distances.append(average_distance)
                max_distances.append(max_distance)
                min_distances.append(min_distance)
                var_distances.append(var)
    # Save to excel file        
    if args.distance_method == 'euclidean' or args.distance_method == 'mahalanobis' or args.distance_method == 'corrected_euclidean':
        df_result = pd.DataFrame({'query_id': output_query_id, 'gallery_id': output_gallery_id, 'average_distances': average_distances
            , 'max_distances': max_distances, 'min_distances': min_distances, 'var_distances': var_distances, 'flag':[dist < 100 for dist in average_distances]})
        output_file = os.path.join(args.output_file, f"{args.cam}.xlsx")
        df_result.to_excel(output_file, index=False)
    
    else:
        df_result = pd.DataFrame({'query_id': output_query_id, 'gallery_id': output_gallery_id, 'distance': output_distances})
        df_result.to_excel(args.output_file, index=False)

if __name__ == '__main__':
    args = make_parser().parse_args()
    main(args)

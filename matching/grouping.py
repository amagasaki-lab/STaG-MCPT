import pandas as pd
import numpy as np
import argparse
import os


def make_parser():
    parser = argparse.ArgumentParser("Grouping according to set conditions.")
    parser.add_argument("--input_file", default='output/distances/', help="Input file directory")
    parser.add_argument("--tracking_file", default='data/single_camera_tracking/', help="MOT file directory")
    parser.add_argument("--output_group_tracking_file", default='output/grouping/', help="output group tracking file")
    parser.add_argument("--cam", default='cameraA', choices=["cameraA", "cameraB", "cameraC"], help="Enter name of camera")
    parser.add_argument("--col_name", default='flag', help="Name of the column containing the conditional expression")
    return parser

def main(args):
    id = 1
    done_id = []

    input_file = os.path.join(args.input_file, f"{args.cam}.xlsx")
    df = pd.read_excel(input_file, sheet_name="Sheet1")

    labels = ["Frame","Id","x","y","w","h","conf","a1","a2","a3"]
    tracking_file = os.path.join(args.tracking_file, f"{args.cam}.txt")
    df2 = pd.read_csv(tracking_file, names=labels)
    df2.insert(2, "group_id", 0)

    # Using distance to create groups
    for count, i in enumerate(df["query_id"].unique()):
        print(f'{count+1} / {len(df["query_id"].unique())}')
        groups = []
        search_id = []
        if i in done_id:
            continue
        condition = df["query_id"] == i
        selected_col = df[condition]

        for index, row in selected_col.iterrows():
            if row[args.col_name] == True:
                search_id.append(row['gallery_id'])
        if len(search_id) > 0:
            groups.append(i)
    
        while len(search_id) !=0:
            groups.append(search_id[0])
            condition = df["query_id"] == search_id[0]
            selected_col = df[condition]
            for index, row in selected_col.iterrows():
                if row[args.col_name] == True:
                    if row['gallery_id'] not in search_id:
                        search_id.append(row['gallery_id'])

            condition = df["gallery_id"] == search_id[0] 
            selected_col = df[condition]
            for index, row in selected_col.iterrows():
                if row[args.col_name] == True:
                    if row['query_id'] not in search_id and row['query_id'] not in groups:
                        search_id.append(row['query_id'])
            search_id.remove(search_id[0]) 
    
        for personal_id in groups:
            done_id.append(personal_id)
            df2.loc[df2['Id'] == personal_id, 'group_id'] = int(id)
        id += 1
    
    output_group_tracking_file = os.path.join(args.output_group_tracking_file, f"{args.cam}.txt")
    df2.to_csv(output_group_tracking_file, sep=",", header=False, index=False)

if __name__ == '__main__':
    args = make_parser().parse_args()
    main(args)
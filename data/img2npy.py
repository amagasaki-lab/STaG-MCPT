# txtとmp4からnpyファイルを出力する
import os
import cv2
import numpy as np
import pandas as pd
import argparse

def make_parser():
    parser = argparse.ArgumentParser("Store information in npy files")
    parser.add_argument("--input_video_path", default='data/movie/cameraA.mp4', help="Input video path")
    parser.add_argument("--output_npy_path", default='data/image/', help="Directory path to output npy file")
    parser.add_argument("--input_txt_path", default='data/single_camera_tracking/', help="Directory path containing tracking results")
    parser.add_argument("--cam", default="cameraA", help="Name of camera")
    parser.add_argument("--start_frame", default=1, type=int, help="Input start frame number")
    parser.add_argument("--end_frame", default=107999, type=int, help="Input end frame number")
    return parser
    

def main(args):

    frame=1
    cap = cv2.VideoCapture(args.input_video_path)
    fps = cap.get(cv2.CAP_PROP_FPS)

    input_txt = os.path.join(args.input_txt_path, f"{args.cam}.txt")
    labels = ["Frame","id","x","y","w","h","conf","a1","a2","a3"]
    df = pd.read_csv(input_txt, names=labels)

    # start_frame ~ end_frameまでnpyファイルに格納する
    results = []
    while True :
        print(f"{frame} / {args.end_frame}")
        ret, img = cap.read()
        if ret == False:
            break
        if args.start_frame <= frame:
            df_filtered = df[df['Frame'] == frame]
            for index, data in df_filtered.iterrows():
                x1, y1, x2, y2 = tuple(map(int, (data[2], data[3], data[2] + data[4], data[3] + data[5])))
                obj_id = int(data[1])
                x_max = max(x1, 0)
                y_max = max(y1, 0)
        
                image_pixel = cv2.resize(img[y_max:y2, x_max:x2], (64, 128), interpolation=cv2.INTER_CUBIC)
                results.append(np.array([obj_id, frame, image_pixel, x1, y1]))

        if frame == args.end_frame:
            print(fps)
            cap.release()
            cv2.destroyAllWindows()
            break
        
        frame +=1
        
    output_npy = os.path.join(args.output_npy_path, f"{args.cam}.npy")
    np.save(output_npy, np.asanyarray(results))



if __name__ == '__main__':
    args = make_parser().parse_args()
    main(args)
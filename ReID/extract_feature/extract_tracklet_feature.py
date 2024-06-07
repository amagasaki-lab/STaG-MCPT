# For feature extraction in MGN (in units of 10 frames).
import torch
from torchvision import transforms
from network import MGN
from tqdm import tqdm
from PIL import Image
import numpy as np
import sys
import argparse

def make_parser():
    parser = argparse.ArgumentParser("Start extract tracklet feature!")
    parser.add_argument("input_npy", help="npy files output from MOT")
    parser.add_argument("model", help="Model weight paths")
    parser.add_argument("cam", choices=["cameraA", "cameraB", "cameraC"], help="Name of camera")
    parser.add_argument("-frame_interval", default=10, help="How many frames apart are the features extracted?")
    parser.add_argument("-save_path", default='output/features/', help="Directory path to be saved")
    parser.add_argument("-tracklet_length", default=30, help="Minimum tracklet length to be tracked")
    return parser

def extract_feature(model, loader):
    features = torch.FloatTensor()
    for (inputs, labels) in loader:
        input_img = inputs.to('cuda')
        outputs = model(input_img)
        f1 = outputs[0].data.cpu()
        inputs = inputs.index_select(3, torch.arange(inputs.size(3) - 1, -1, -1))       
        input_img = inputs.to('cuda')
        outputs = model(input_img)
        f2 = outputs[0].data.cpu()
        ff = f1 + f2
        fnorm = torch.norm(ff, p=2, dim=1, keepdim=True) 
        ff = ff.div(fnorm.expand_as(ff))      
        features = torch.cat((features, ff), 0)
    return features


class Extract_Information:
    def __init__(self, cam, interval, min_length, transform, model):
        self.cam = cam
        self.interval = interval
        self.min_length = min_length
        self.transform = transform
        self.model = model

    def extract_tracklet_feature(self, dataset_list, x_id):
        frame_list = []
        xy_list = []
        id_feature = torch.FloatTensor()
        count = 0

        for file in tqdm(dataset_list):
            if int(file[0]) == x_id:
                if count % self.interval == 0:
                    pil_image = Image.fromarray(file[2])
                    img = self.transform(pil_image)
                    feature = extract_feature(self.model, [(torch.unsqueeze(img, 0), 1)]) 
                    id_feature = torch.cat((id_feature, feature), 0)
                frame_list.append(file[1])
                xy_list.append([file[1], file[3], file[4]])
                count += 1
        return id_feature, frame_list, xy_list, count
    
    def time_information(self, frame_list): 
        '''
        This is to synchronize the time as the fps differs from camera to camera.
        Adjust it yourself depending on the camera.
        '''
        frame_min = min(frame_list)
        if self.cam == 'cameraC':
            frame_min = frame_min * 1.00
        elif self.cam == 'cameraB':
            frame_min = frame_min * 1.27
        return frame_min
    
    def dir_information(self, locate_list):
        locate_max = np.argmax(locate_list, axis=0) 
        locate_min = np.argmin(locate_list, axis=0) 
        start_point = np.array([locate_list[locate_min[0]][1], locate_list[locate_min[0]][2]]) 
        end_point = np.array([locate_list[locate_max[0]][1], locate_list[locate_max[0]][2]]) 
        vec = end_point - start_point
        angle = np.rad2deg(np.arctan2(vec[0], vec[1]))
        if self.cam == 'cameraA':
            if (angle < 45) and (angle > -135):
                dir = 1
            else:
                dir = 2
        elif self.cam == 'cameraC':
            if angle > 0:
                dir = 1
            else:
                dir = 2
        elif self.cam == 'cameraB':
            if (angle < -90) or (angle > 90):
                dir = 1
            else:
                dir = 2
        else:
            print('Input value "cam" is unexpected.')
            sys.exit()
        return dir


def main(args):
    model = MGN()
    model.load_state_dict(torch.load(args.model, map_location=torch.device('cuda'))) 
    model = model.to('cuda')
    model.eval() # 評価モード
    transform = transforms.Compose([
            transforms.Resize((384, 128), interpolation=3),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])])
    
    extract_information = Extract_Information(args.cam, args.frame_interval, args.tracklet_length, transform, model)
    database = []
    dataset_list = np.load(args.input_npy, allow_pickle=True)
    id_list = dataset_list[:,0]
    max_id = max(id_list)
    track_id = -1

    while True:
        track_id += 1
        print(f"{track_id}/{max_id}")
        if track_id > max_id:
            break

        id_feature, frame_list, xy_list, counter  = extract_information.extract_tracklet_feature(dataset_list, track_id) 
        if counter < args.tracklet_length:
            continue

        frame_min = extract_information.time_information(frame_list)
        dir = extract_information.dir_information(xy_list)
        id_feature_mean = torch.mean(id_feature, 0, True) 
        id_feature_mean_np = id_feature_mean.cpu().detach().numpy().copy()
        id_feature = [id_feature_mean_np[0], track_id, frame_min, dir]

        database.append(id_feature)

    database = np.array(database)
    np.save(args.save_path + f"{args.cam}_feature.npy", database)

if __name__ == '__main__':
    args = make_parser().parse_args()
    main(args)
    print("Saved successfully!")
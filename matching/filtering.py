import warnings

class Filtering:
    def __init__(self, query_place, gallery_place, query_group_frame=None, query_group_dir=None, query_groups=None, gallery_group_frame=None, gallery_group_dir=None):
        self.query_place = query_place
        self.gallery_place = gallery_place
        self.query_group_frame = query_group_frame
        self.query_groups = query_groups
        self.gallery_group_frame = gallery_group_frame
        self.query_group_dir = query_group_dir
        self.gallery_group_dir = gallery_group_dir

    def filtering_info(self, query_dir):
        if self.gallery_place == 'cameraB':
            if self.query_place == 'cameraC':
                min_frame, max_frame = (4000, 34000) if query_dir == 1 else (4000, 34000) 
            elif self.query_place == 'cameraA':
                min_frame, max_frame = (6000, 34000) if query_dir == 1 else (6000, 34000) 
            else:
                warnings.warn('Input value "cam" is unexpected', UserWarning)

        elif self.gallery_place == 'cameraC':
            if self.query_place == 'cameraB':
                min_frame, max_frame = (4000, 34000) if query_dir == 1 else (4000, 34000) 
            elif self.query_place == 'cameraA':
                min_frame, max_frame = 0, 18000
            else:
                warnings.warn('Input value "cam" is unexpected', UserWarning)

        elif self.gallery_place == 'cameraA':
            if self.query_place == 'cameraB':
                min_frame, max_frame = (6000, 34000) if query_dir == 1 else (6000, 34000) 
            elif self.query_place == 'cameraC':
                min_frame, max_frame = 0, 18000
            else:
                warnings.warn('Input value "cam" is unexpected', UserWarning)

        else:
            warnings.warn('Input value "cam" is unexpected', UserWarning)
        return min_frame, max_frame
    
    def filtering_group_process(self, query_id, min_frame, max_frame):
        indices = [row for row, item in enumerate(self.query_groups) if query_id in item][0]
        query_dir = self.query_group_dir[indices]
        query_frame = self.query_group_frame[indices]
        condition_dir = [True if item == query_dir else False for item in self.gallery_group_dir]
        condition_frame = []
        for gallery_frame in self.gallery_group_frame:
            if query_dir == 1:
                if ((self.gallery_place == 'cameraA') or ((self.gallery_place == 'cameraC') and (self.query_place == 'cameraB'))):
                    if (((gallery_frame - query_frame) > min_frame) and ((gallery_frame - query_frame) < max_frame)):
                        condition_frame.append(True)
                    else:
                        condition_frame.append(False)
                else:
                    if (((query_frame - gallery_frame) > min_frame) and ((query_frame - gallery_frame) < max_frame)):
                        condition_frame.append(True)
                    else:
                        condition_frame.append(False)
            else:
                if ((self.gallery_place == 'cameraA') or ((self.gallery_place == 'cameraC') and (self.query_place == 'cameraB'))):
                    if (((query_frame - gallery_frame) > min_frame) and ((query_frame - gallery_frame) < max_frame)):
                        condition_frame.append(True)
                    else:
                        condition_frame.append(False)
                else:
                    if (((gallery_frame - query_frame) > min_frame) and ((gallery_frame - query_frame) < max_frame)):
                        condition_frame.append(True)
                    else:
                        condition_frame.append(False)
        filtering_result = [True if x and y else False for x, y in zip(condition_dir, condition_frame)]
        return filtering_result
    
    def filtering_individual_process(self, query_id, min_frame, max_frame):
        indices = [row for row, item in enumerate(self.query_groups) if query_id in item][0]
        query_dir = self.query_group_dir[indices]
        query_frame = self.query_group_frame[indices]
        condition_dir = [True if item == query_dir else False for item in self.gallery_group_dir]
        condition_frame = []
        for gallery_frame in self.gallery_group_frame:
            if query_dir == 1:
                if ((self.gallery_place == 'cameraA') or ((self.gallery_place == 'cameraC') and (self.query_place == 'cameraB'))):
                    if (((gallery_frame - query_frame) > min_frame) and ((gallery_frame - query_frame) < max_frame)):
                        condition_frame.append(True)
                    else:
                        condition_frame.append(False)
                else:
                    if (((query_frame - gallery_frame) > min_frame) and ((query_frame - gallery_frame) < max_frame)):
                        condition_frame.append(True)
                    else:
                        condition_frame.append(False)
            else:
                if ((self.gallery_place == 'cameraA') or ((self.gallery_place == 'cameraC') and (self.query_place == 'cameraB'))):
                    if (((query_frame - gallery_frame) > min_frame) and ((query_frame - gallery_frame) < max_frame)):
                        condition_frame.append(True)
                    else:
                        condition_frame.append(False)
                else:
                    if (((gallery_frame - query_frame) > min_frame) and ((gallery_frame - query_frame) < max_frame)):
                        condition_frame.append(True)
                    else:
                        condition_frame.append(False)
        filtering_result = [True if x and y else False for x, y in zip(condition_dir, condition_frame)]
        return filtering_result
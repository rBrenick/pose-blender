class ModuleConstants:
    extension_file_prefix = "pose_blender_ext"


class PoseAsset(object):
    def __init__(self):
        self.local_path = ""
        self.pose_name = ""
        self.pose_data = None
        self.thumbnail_data = None

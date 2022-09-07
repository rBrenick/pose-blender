class ModuleConstants:
    extension_file_prefix = "pose_blender_ext"


class PoseAsset(object):
    def __init__(self):
        self.local_path = ""
        self.pose_name = ""
        self.pose_data = None
        self.thumbnail_image = None  # type: QtGui.QImage
        self.is_favorite = False

        # p4
        self.needs_sync = True

    def update(self):
        pass

    def set_thumbnail_data(self):
        """
        Function that runs in a thread to parse thumbnail data from disk
        """
        pass

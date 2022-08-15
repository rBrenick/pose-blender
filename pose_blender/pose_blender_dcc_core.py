from . import pose_blender_constants as k
from . import pose_blender_logger

log = pose_blender_logger.get_logger()


class PoseBlenderCoreInterface(object):

    def log_missing_implementation(self, func):
        log.error("'{}.{}()' has not been implemented".format(self.__class__.__name__, func.__name__))

    ######################################################################################
    # Required Project/Studio implementations

    def get_rigs_in_scene(self):
        self.log_missing_implementation(self.get_rigs_in_scene)
        return {"Example Rig": None}  # {rig_name: rig_node}

    def get_poses(self):
        self.log_missing_implementation(self.get_poses)

        # example setup
        pose_assets = []

        asset_1 = k.PoseAsset()
        asset_1.pose_name = "Example Pose 1"
        pose_assets.append(asset_1)

        asset_2 = k.PoseAsset()
        asset_2.pose_name = "Example Pose 2"
        pose_assets.append(asset_2)

        return pose_assets  # type: [k.PoseAsset]

    def apply_pose_asset(self, pose_asset, rig_name, on_selected=True):
        pass

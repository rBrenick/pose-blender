from . import pose_blender_constants as k
from . import pose_blender_logger

log = pose_blender_logger.get_logger()


class PoseBlenderCoreInterface(object):
    def __init__(self):
        self.active_rig = None

        # every time you click a pose, this will be set
        self.selected_pose = None

        # when you start blending poses, the active pose will be set
        self.blend_pose = None

        self.blend_pre_values = {}
        self.blend_post_values = {}

        self.blend_ignore_attr_names = []

        self.right_click_menu_items = []

    def log_missing_implementation(self, func):
        log.error("'{}.{}()' has not been implemented".format(self.__class__.__name__, func.__name__))

    ######################################################################################
    # implementations come pre-built

    def set_blend_pose(self, pose_asset):
        self.blend_pose = pose_asset

    def cache_pre_blend(self, active_rig):
        self.blend_pre_values = self.get_control_values(active_rig)

    def cache_blend_target(self, active_rig):
        self.blend_post_values = self.get_control_values(active_rig)

    def get_control_values(self, active_rig):
        return {}

    def blend_cached_pose(self, weight):
        pass

    def remove_caches(self):
        self.blend_pose = None
        self.blend_pre_values = {}
        self.blend_post_values = {}

    def get_controllers(self, active_rig):
        return []

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

    def apply_pose_asset(self, pose_asset, rig_name):
        pass

    ######################################################################################
    # Optional implementations

    def set_pose_favorite_state(self, pose_asset, state=True):
        self.log_missing_implementation(self.set_pose_favorite_state)
        pass

    def get_project_widgets(self):
        return []

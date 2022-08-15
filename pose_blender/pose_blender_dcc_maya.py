import pymel.core as pm
from . import pose_blender_dcc_core


class PoseBlenderMaya(pose_blender_dcc_core.PoseBlenderCoreInterface):
    def __init__(self):
        self.active_pose = None
        self.blend_pre_values = {}
        self.blend_post_values = {}

    def set_active_pose(self, pose_asset):
        self.active_pose = pose_asset

    def cache_pre_blend(self, active_rig):
        self.blend_pre_values = self.get_control_values(active_rig)

    def cache_blend_target(self, active_rig):
        self.blend_post_values = self.get_control_values(active_rig)

    def get_controllers(self, active_rig):
        return pm.selected()

    def get_control_values(self, active_rig):
        current_pose = {}
        for controls in self.get_controllers(active_rig):
            for a in controls.listAttr(keyable=True, userDefined=False):
                if "space" in a.attrName():
                    continue
                current_pose[a] = a.get()
        return current_pose

    def blend_cached_pose(self, weight):
        for attr, pre_val in self.blend_pre_values.items():
            target_val = self.blend_post_values.get(attr)

            blend_result = float_lerp(pre_val, target_val, weight)
            attr.set(blend_result)

    def remove_caches(self):
        self.active_pose = None
        self.blend_pre_values = {}
        self.blend_post_values = {}


def float_lerp(float_a, float_b, interp_val):
    return float_a + (float_b - float_a) * interp_val

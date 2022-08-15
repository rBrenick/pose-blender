import pymel.core as pm
from . import pose_blender_dcc_core


class PoseBlenderMaya(pose_blender_dcc_core.PoseBlenderCoreInterface):
    def __init__(self):
        self.active_pose = None
        self.pre_blend_values = {}
        self.blend_target_values = {}

    def set_active_pose(self, pose_asset):
        self.active_pose = pose_asset

    def cache_pre_blend(self, active_rig):
        self.pre_blend_values = self.get_control_values(active_rig)

    def cache_blend_target(self, active_rig):
        self.blend_target_values = self.get_control_values(active_rig)

    def get_control_values(self, active_rig):
        current_pose = {}
        for controls in pm.selected():
            for a in controls.listAttr(keyable=True, userDefined=False):
                if "space" in a.attrName():
                    continue
                current_pose[a] = a.get()
        return current_pose

    def blend_cached_pose(self, weight):
        for attr, pre_val in self.pre_blend_values.items():
            target_val = self.blend_target_values.get(attr)

            blend_result = float_lerp(pre_val, target_val, weight)
            attr.set(blend_result)


def float_lerp(float_a, float_b, interp_val):
    return float_a + (float_b - float_a) * interp_val

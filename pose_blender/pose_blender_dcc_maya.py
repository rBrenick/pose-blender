import pymel.core as pm
from . import pose_blender_dcc_core


class PoseBlenderMaya(pose_blender_dcc_core.PoseBlenderCoreInterface):

    def __init__(self):
        super(PoseBlenderMaya, self).__init__()

    def get_controllers(self, active_rig):
        return pm.selected()

    def get_control_values(self, active_rig):
        current_pose = {}
        for controls in self.get_controllers(active_rig):
            for a in controls.listAttr(keyable=True, userDefined=False):
                if a.attrName() in self.blend_ignore_attr_names:
                    continue
                current_pose[a] = a.get()
        return current_pose

    def blend_cached_pose(self, weight):
        for attr, pre_val in self.blend_pre_values.items():
            target_val = self.blend_post_values.get(attr)

            blend_result = float_lerp(pre_val, target_val, weight)
            attr.set(blend_result)


def float_lerp(float_a, float_b, interp_val):
    return float_a + (float_b - float_a) * interp_val

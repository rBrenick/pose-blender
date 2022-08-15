def main(*args, **kwargs):
    from . import pose_blender_ui
    return pose_blender_ui.main(*args, **kwargs)


def reload_modules():
    import sys
    if sys.version_info.major >= 3:
        from importlib import reload
    else:
        from imp import reload
    
    from . import pose_blender_constants
    from . import pose_blender_logger
    from . import pose_blender_dcc_core
    from . import pose_blender_dcc_maya
    from . import pose_blender_system
    from . import pose_blender_ui
    reload(pose_blender_constants)
    reload(pose_blender_logger)
    reload(pose_blender_dcc_core)
    reload(pose_blender_dcc_maya)
    reload(pose_blender_system)
    reload(pose_blender_ui)
    pose_blender_system.import_extensions(refresh=True)
    reload(pose_blender_system)


def startup():
    # from maya import cmds
    # cmds.optionVar(query="") # example of finding a maya optionvar
    pass





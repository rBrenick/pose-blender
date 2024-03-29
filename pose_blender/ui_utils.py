import os
import sys
from functools import partial

from PySide2 import QtCore, QtWidgets, QtGui
from shiboken2 import wrapInstance

if sys.version_info.major >= 3:
    long = int

active_dcc_is_maya = "maya" in os.path.basename(sys.executable).lower()
active_dcc_is_houdini = "houdini" in os.path.basename(sys.executable).lower()

standalone_app_window = None

resources_folder = os.path.join(os.path.dirname(os.path.dirname(__file__)), "resources")


def get_app_window():
    top_window = standalone_app_window

    if active_dcc_is_maya:
        from maya import OpenMayaUI as omui
        maya_main_window_ptr = omui.MQtUtil().mainWindow()
        top_window = wrapInstance(long(maya_main_window_ptr), QtWidgets.QMainWindow)

    elif active_dcc_is_houdini:
        import hou
        top_window = hou.qt.mainWindow()

    return top_window


class CoreToolWindow(QtWidgets.QMainWindow):
    def __init__(self, parent=None):
        if parent is None:
            parent = get_app_window()
        super(CoreToolWindow, self).__init__(parent)

        self.ui = None
        self.setWindowTitle(self.__class__.__name__)

    def main(self, *args, **kwargs):
        self.show()

    def on_close(self):
        """for easy overloading with maya dockable windows"""
        pass

    #########################################################
    # convenience functions to make a simple button layout

    def ensure_main_layout(self):
        if self.ui is None:
            main_widget = QtWidgets.QWidget()
            main_layout = QtWidgets.QVBoxLayout()
            main_widget.setLayout(main_layout)
            self.ui = main_widget
            self.setCentralWidget(main_widget)

    def add_button(self, text, command, clicked_args=None):
        self.ensure_main_layout()

        main_layout = self.ui.layout()

        btn = QtWidgets.QPushButton(text)
        btn.setSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Minimum)
        main_layout.addWidget(btn)

        if clicked_args:
            btn.clicked.connect(partial(command, *clicked_args))
        else:
            btn.clicked.connect(command)


class WindowCache:
    window_instances = {}


if active_dcc_is_maya:

    from maya.app.general import mayaMixin
    from maya import OpenMayaUI as omui
    from maya import cmds

    class ToolWindow(mayaMixin.MayaQWidgetDockableMixin, CoreToolWindow):

        WORKSPACE_NAMES = []

        def __init__(self, parent=None):
            if parent is None:
                parent = get_app_window()
            super(ToolWindow, self).__init__(parent=parent)
            self.setAttribute(QtCore.Qt.WA_DeleteOnClose)

        def main(self, restore=False, refresh=False):
            if restore:
                restored_control = omui.MQtUtil.getCurrentParent()
                mixin_ptr = omui.MQtUtil.findControl(self.objectName())
                omui.MQtUtil.addWidgetToMayaLayout(long(mixin_ptr), long(restored_control))

                self.WORKSPACE_NAMES.append(self.parent().objectName())
                return self

            if refresh:
                opened_workspaces = list(self.WORKSPACE_NAMES)
                for workspace_name in opened_workspaces:
                    try:
                        remove_workspace(workspace_name)
                        self.WORKSPACE_NAMES.remove(workspace_name)
                    except Exception as e:
                        print(e)

            launch_ui_script = "import {module}; {module}.{class_name}().main(restore=True)".format(
                module=self.__class__.__module__,
                class_name=self.__class__.__name__,
            )

            self.show(dockable=True, height=500, width=700, uiScript=launch_ui_script)

            self.WORKSPACE_NAMES.append(self.parent().objectName())
            return self

        def hideEvent(self, *args):
            if not self.isVisible():
                self.on_close()
            super(ToolWindow, self).hideEvent(*args)

    def remove_workspace(workspace_control_name):
        if cmds.workspaceControl(workspace_control_name, q=True, exists=True):
            cmds.workspaceControl(workspace_control_name, e=True, close=True)
            cmds.deleteUI(workspace_control_name, control=True)


else:
    ToolWindow = CoreToolWindow


def build_menu_from_action_list(actions, menu=None, is_sub_menu=False):
    if not menu:
        menu = QtWidgets.QMenu()

    for action in actions:
        if action == "-":
            menu.addSeparator()
            continue

        for action_title, action_command in action.items():
            if action_title == "RADIO_SETTING":
                # Create RadioButtons for QSettings object
                settings_obj = action_command.get("settings")  # type: QtCore.QSettings
                settings_key = action_command.get("settings_key")  # type: str
                choices = action_command.get("choices")  # type: list
                default_choice = action_command.get("default")  # type: str
                on_trigger_command = action_command.get("on_trigger_command")  # function to trigger after setting value

                # Has choice been defined in settings?
                item_to_check = settings_obj.value(settings_key)

                # If not, read from default option argument
                if not item_to_check:
                    item_to_check = default_choice

                grp = QtWidgets.QActionGroup(menu)
                for choice_key in choices:
                    action = QtWidgets.QAction(choice_key, menu)
                    action.setCheckable(True)

                    if choice_key == item_to_check:
                        action.setChecked(True)

                    action.triggered.connect(partial(
                        set_settings_value,
                        settings_obj,
                        settings_key,
                        choice_key,
                        on_trigger_command
                    ))
                    menu.addAction(action)
                    grp.addAction(action)

                grp.setExclusive(True)
                continue

            if isinstance(action_command, list):
                sub_menu = menu.addMenu(action_title)
                build_menu_from_action_list(action_command, menu=sub_menu, is_sub_menu=True)
                continue

            atn = menu.addAction(action_title)
            atn.triggered.connect(action_command)

    if not is_sub_menu:
        cursor = QtGui.QCursor()
        menu.exec_(cursor.pos())

    return menu


def set_settings_value(settings_obj, key, value, post_set_command=None):
    settings_obj.setValue(key, value)
    if post_set_command:
        post_set_command()





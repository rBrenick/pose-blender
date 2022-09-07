import sys
import threading

from . import resources as resources
from . import pose_blender_constants as k
from . import pose_blender_logger
from . import pose_blender_system as pbs
from . import ui_utils
from .ui_utils import QtCore, QtGui, QtWidgets

log = pose_blender_logger.get_logger()

standalone_app = None
if not QtWidgets.QApplication.instance():
    standalone_app = QtWidgets.QApplication(sys.argv)

    from .resources import stylesheets
    stylesheets.apply_standalone_stylesheet()


class PoseBlenderWidget(QtWidgets.QWidget):
    def __init__(self, *args, **kwargs):
        super(PoseBlenderWidget, self).__init__(*args, **kwargs)

        self.ui = PoseBlenderUI()
        main_layout = QtWidgets.QVBoxLayout()
        main_layout.setContentsMargins(2, 2, 2, 2)
        main_layout.addWidget(self.ui)
        self.setLayout(main_layout)

        self.blender_engine = None

        for proj_widget in pbs.dcc.get_project_widgets():
            self.ui.project_widget_layouts.addWidget(proj_widget)

        self.ui.rig_chooser.currentTextChanged.connect(self.set_choosen_rig)
        self.ui.refresh_rigs.clicked.connect(self.update_from_scene)
        self.ui.refresh_poses.clicked.connect(self.refresh_poses)
        self.ui.pose_filter.textChanged.connect(self.filter_poses)
        self.ui.grid_toggle.clicked.connect(self.toggle_icon_mode)
        self.ui.size_slider.valueChanged.connect(self.update_pose_size)

        self.refresh_poses()
        self.update_from_scene()

    def refresh_poses(self):
        self.ui.pose_grid.clear()

        for pose_asset in pbs.dcc.get_poses():  # type: k.PoseAsset
            pose_widget = PoseWidget(self, pose_asset)
            pose_widget.apply_pose.connect(self.apply_pose)
            pose_widget.start_blending.connect(self.initialize_blender_engine)
            pose_widget.blend_active_pose.connect(self.blend_active_pose)

            # Create widget
            widget = QtWidgets.QWidget()
            widget.setToolTip(pose_asset.pose_name)

            pose_label = QtWidgets.QLabel()
            pose_label.setAlignment(QtCore.Qt.AlignCenter)
            pose_label.setText(pose_asset.pose_name)
            pose_label.setSizePolicy(QtWidgets.QSizePolicy.Ignored, QtWidgets.QSizePolicy.Minimum)

            widget_layout = QtWidgets.QBoxLayout(QtWidgets.QBoxLayout.Down)
            widget_layout.addWidget(pose_widget)
            widget_layout.addWidget(pose_label)
            widget_layout.setContentsMargins(3, 3, 3, 3)
            widget_layout.setSpacing(0)
            widget_layout.setSizeConstraint(QtWidgets.QLayout.SetFixedSize)
            widget.setLayout(widget_layout)

            # add to grid
            lwi = QtWidgets.QListWidgetItem()
            lwi.setSizeHint(widget.sizeHint())
            self.ui.pose_grid.addItem(lwi)
            self.ui.pose_grid.setItemWidget(lwi, widget)
            lwi.setData(QtCore.Qt.UserRole, pose_widget)
            pose_widget.item_main_widget = widget
            pose_widget.list_widget_item = lwi
            pose_widget.item_label = pose_label

        self.refresh_grid_display()
        self.start_thumbnail_thread()

    def start_thumbnail_thread(self):
        thumbnail_thread = threading.Thread(target=self.generate_thumbnails)
        thumbnail_thread.start()

    def generate_thumbnails(self):
        for pose_widget in self.get_pose_widgets():  # type: PoseWidget
            try:
                pose_widget.set_thumbnail_from_pose_asset(from_disk=True)
            except Exception as e:
                log.warning("Failed to parse thumbnail data from: {} - {}".format(pose_widget.pose_asset.pose_name, e))

    def update_from_scene(self):
        rig_names = list(pbs.dcc.get_rigs_in_scene().keys())
        self.ui.rig_chooser.clear()
        self.ui.rig_chooser.addItems(rig_names)

    def initialize_blender_engine(self, pose_asset):
        if pbs.dcc.blend_pose == pose_asset:
            log.info("same pose asset, keeping existing blender engine")
            return

        log.info("Starting Pose Blender Engine")
        self.blender_engine = pbs.dcc.set_blend_pose(pose_asset)
        pbs.dcc.cache_pre_blend(self.get_active_rig())
        pbs.dcc.apply_pose_asset(
            pose_asset,
            self.get_active_rig(),
        )
        pbs.dcc.cache_blend_target(self.get_active_rig())
        pbs.dcc.blend_cached_pose(weight=0)
        log.info("Started Engine")

    def blend_active_pose(self, weight):
        pbs.dcc.blend_cached_pose(weight)

    def apply_pose(self, pose_asset):
        pbs.dcc.apply_pose_asset(
            pose_asset,
            self.get_active_rig(),
        )
        pbs.dcc.remove_caches()

    def filter_poses(self, filter_text):
        for pose_widget in self.get_pose_widgets():  # type: PoseWidget
            pose_widget.list_widget_item.setHidden(False)
            if filter_text.lower() not in pose_widget.pose_asset.pose_name.lower():
                pose_widget.list_widget_item.setHidden(True)

    def update_pose_size(self, new_size):
        for pose_widget in self.get_pose_widgets():  # type: PoseWidget
            pose_widget.update_size(new_size)
        self.ui.pose_grid.doItemsLayout()

    def get_pose_widgets(self):
        return [lwi.data(QtCore.Qt.UserRole) for lwi in self.get_pose_list_widgets()]

    def get_pose_list_widgets(self):
        list_widgets = []
        for item_index in range(self.ui.pose_grid.count()):
            lwi = self.ui.pose_grid.item(item_index)  # type: QtWidgets.QListWidgetItem
            list_widgets.append(lwi)
        return list_widgets

    def get_active_rig(self):
        return self.ui.rig_chooser.currentText()

    def set_choosen_rig(self, rig_name):
        pbs.dcc.active_rig = rig_name
        log.info("Set active rig: {}".format(rig_name))

    def refresh_grid_display(self):
        if self.ui.pose_grid.viewMode() == QtWidgets.QListWidget.IconMode:
            layout_dir = QtWidgets.QBoxLayout.Down
            label_size_policy = QtWidgets.QSizePolicy.Ignored, QtWidgets.QSizePolicy.Minimum
        else:
            layout_dir = QtWidgets.QBoxLayout.LeftToRight
            label_size_policy = QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Minimum

        # update pose widget display
        for pose_widget in self.get_pose_widgets():  # type: PoseWidget
            layout = pose_widget.item_main_widget.layout()  # type: QtWidgets.QBoxLayout
            pose_label = pose_widget.item_label

            layout.setDirection(layout_dir)
            pose_label.setSizePolicy(*label_size_policy)

        self.update_pose_size(self.ui.size_slider.value())

    def toggle_icon_mode(self):
        if self.ui.pose_grid.viewMode() == QtWidgets.QListWidget.IconMode:
            self.ui.pose_grid.setViewMode(QtWidgets.QListWidget.ListMode)
        else:
            self.ui.pose_grid.setViewMode(QtWidgets.QListWidget.IconMode)
        self.refresh_grid_display()


class PoseWidget(QtWidgets.QPushButton):
    apply_pose = QtCore.Signal(k.PoseAsset)

    start_blending = QtCore.Signal(k.PoseAsset)
    blend_active_pose = QtCore.Signal(float)

    def __init__(self, parent, pose_asset):
        """
        Args:
            parent:
            pose_asset (k.PoseAsset):
        """
        super(PoseWidget, self).__init__(parent)

        self.pose_asset = pose_asset
        self.list_widget_item = None  # type: QtWidgets.QListWidgetItem
        self.item_main_widget = None  # type: QtWidgets.QListWidgetItem
        self.item_label = None # type: QtWidgets.QLabel
        self.image_size = 180

        self.set_thumbnail_from_pose_asset()
        self.update_size(self.image_size)

        self.value_display_overlay = ValueDisplayOverlay(self)
        self.value_display_overlay.setVisible(False)

        self.set_favorite_display()

    def mousePressEvent(self, event):
        pbs.dcc.selected_pose = self.pose_asset

        if event.buttons() == QtCore.Qt.MidButton:
            self.start_blending.emit(self.pose_asset)

        elif event.buttons() == QtCore.Qt.LeftButton:

            if self.pose_asset.needs_sync:
                self.pose_asset.update()
                self.set_thumbnail_from_pose_asset()
                event.accept()
                return

            self.trigger_apply_pose()

        elif event.buttons() == QtCore.Qt.RightButton:

            action_list = [
                {"Apply Pose": self.trigger_apply_pose},
                "-"
            ]

            if self.pose_asset.is_favorite:
                action_list.append({"Un-Favorite": self.remove_pose_as_favorite})
            else:
                action_list.append({"Favorite": self.set_pose_as_favorite})
            action_list.append("-")

            action_list.extend(pbs.dcc.right_click_menu_items)
            ui_utils.build_menu_from_action_list(action_list)

        event.accept()

    def mouseReleaseEvent(self, event):
        self.value_display_overlay.setVisible(False)

    def mouseMoveEvent(self, event):
        if event.buttons() == QtCore.Qt.MidButton:
            weight_value = 1.0 - event.y() / self.image_size
            self.blend_active_pose.emit(weight_value)

            # update display
            self.value_display_overlay.weight = weight_value
            self.value_display_overlay.setVisible(True)
            self.value_display_overlay.repaint()

    def resizeEvent(self, event):
        self.value_display_overlay.resize(event.size())
        event.accept()

    def update_size(self, size):
        margin = size * 0.1
        self.image_size = size
        self.setMinimumWidth(self.image_size)
        self.setMinimumHeight(self.image_size)
        self.setIconSize(QtCore.QSize(self.image_size - margin, self.image_size - margin))

        if self.list_widget_item and self.item_main_widget:
            self.list_widget_item.setSizeHint(self.item_main_widget.sizeHint())

    def trigger_apply_pose(self):
        self.apply_pose.emit(self.pose_asset)

    def set_pose_as_favorite(self):
        pbs.dcc.set_pose_favorite_state(self.pose_asset, True)
        self.set_favorite_display()

    def remove_pose_as_favorite(self):
        pbs.dcc.set_pose_favorite_state(self.pose_asset, False)
        self.set_favorite_display()

    def set_thumbnail_from_pose_asset(self, from_disk=False):
        if from_disk:
            self.pose_asset.set_thumbnail_data()

        if self.pose_asset.needs_sync:
            thumbnail = QtGui.QImage(resources.get_image_path("p4_out_of_sync"))
        else:
            if self.pose_asset.thumbnail_image:
                thumbnail = self.pose_asset.thumbnail_image
            else:
                thumbnail = QtGui.QImage(resources.get_image_path("undefined"))

        icon = QtGui.QIcon()
        pixmap = QtGui.QPixmap.fromImage(thumbnail)
        icon.addPixmap(pixmap)
        self.setIcon(icon)

    def set_favorite_display(self):
        if self.pose_asset.is_favorite:
            self.setStyleSheet("background-color: rgb(255, 211, 57)")
        else:
            self.setStyleSheet("")


class ValueDisplayOverlay(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super(ValueDisplayOverlay, self).__init__(parent)

        self.weight = 0.0

        palette = QtGui.QPalette(self.palette())
        palette.setColor(palette.Background, QtCore.Qt.transparent)
        self.setPalette(palette)

    def paintEvent(self, event):
        painter = QtGui.QPainter()
        painter.begin(self)
        painter.fillRect(event.rect(), QtGui.QBrush(QtGui.QColor(100, 100, 100, 100)))
        painter.drawText(event.rect(), QtCore.Qt.AlignCenter, str(round(self.weight, 2)))
        painter.setFont(QtGui.QFont("seqoe", 13))
        painter.setPen(QtGui.QPen(QtCore.Qt.NoPen))


class PoseBlenderUI(QtWidgets.QWidget):
    def __init__(self, *args, **kwargs):
        super(PoseBlenderUI, self).__init__(*args, **kwargs)

        self.pose_filter = QtWidgets.QLineEdit()
        self.pose_filter.setPlaceholderText("Search...")
        self.pose_filter.setClearButtonEnabled(True)

        self.size_slider = QtWidgets.QSlider()
        self.size_slider.setOrientation(QtCore.Qt.Horizontal)
        self.size_slider.setRange(20, 960)
        self.size_slider.setValue(180)

        self.grid_toggle = QtWidgets.QPushButton("List/Grid")
        self.refresh_poses = QtWidgets.QPushButton("Refresh")

        self.pose_grid = QtWidgets.QListWidget()
        self.pose_grid.setVerticalScrollMode(QtWidgets.QListWidget.ScrollPerPixel)
        self.pose_grid.setViewMode(QtWidgets.QListWidget.IconMode)
        self.pose_grid.setResizeMode(QtWidgets.QListWidget.Adjust)
        self.pose_grid.setLayoutMode(QtWidgets.QListWidget.Batched)

        self.project_widget_layouts = QtWidgets.QVBoxLayout()

        self.rig_chooser = QtWidgets.QComboBox()
        self.refresh_rigs = QtWidgets.QPushButton("Refresh")
        self.refresh_rigs.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)

        main_layout = QtWidgets.QVBoxLayout()
        main_layout.setSpacing(2)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(self.pose_filter)

        grid_controls_layout = QtWidgets.QHBoxLayout()
        grid_controls_layout.addWidget(self.size_slider)
        grid_controls_layout.addWidget(self.grid_toggle)
        grid_controls_layout.addWidget(self.refresh_poses)
        main_layout.addLayout(grid_controls_layout)

        main_layout.addWidget(self.pose_grid)

        rig_layout = QtWidgets.QHBoxLayout()
        rig_layout.addWidget(self.rig_chooser)
        rig_layout.addWidget(self.refresh_rigs)
        main_layout.addLayout(rig_layout)

        main_layout.addLayout(self.project_widget_layouts)
        self.setLayout(main_layout)


class PoseBlenderWindow(ui_utils.ToolWindow):
    def __init__(self):
        super(PoseBlenderWindow, self).__init__()
        self.main_widget = PoseBlenderWidget()
        self.setCentralWidget(self.main_widget)
        self.setWindowTitle("Pose Blender")


def main(refresh=False):
    win = PoseBlenderWindow()
    win.main(refresh=refresh)

    if standalone_app:
        ui_utils.standalone_app_window = win
        sys.exit(standalone_app.exec_())

    return win


if __name__ == "__main__":
    main()

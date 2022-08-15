import sys

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

        for pose_asset in pbs.dcc.get_poses():  # type: k.PoseAsset
            pose_widget = PoseWidget(self, pose_asset)
            pose_widget.apply_pose.connect(self.apply_pose)
            pose_widget.start_blending.connect(self.initialize_blender_engine)
            pose_widget.blend_active_pose.connect(self.blend_active_pose)

            # Create widget
            widget = QtWidgets.QWidget()
            widget.setStyleSheet("background-color: (100, 100, 100)")
            widget.setToolTip(pose_asset.pose_name)

            pose_label = QtWidgets.QLabel()
            pose_label.setAlignment(QtCore.Qt.AlignCenter)
            pose_label.setText(pose_asset.pose_name)
            pose_label.setSizePolicy(QtWidgets.QSizePolicy.Ignored, QtWidgets.QSizePolicy.Minimum)

            widget_layout = QtWidgets.QVBoxLayout()
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
            pose_widget.list_widget_widget = widget
            pose_widget.list_widget_item = lwi

        rig_names = list(pbs.dcc.get_rigs_in_scene().keys())
        self.ui.rig_chooser.addItems(rig_names)

        self.ui.pose_filter.textChanged.connect(self.filter_poses)
        self.ui.size_slider.valueChanged.connect(self.update_pose_size)

    def initialize_blender_engine(self, pose_asset):
        if pbs.dcc.active_pose == pose_asset:
            log.info("same pose asset, keeping existing blender engine")
            return

        log.info("Starting Pose Blender Engine")
        self.blender_engine = pbs.dcc.set_active_pose(pose_asset)
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
        self.list_widget_widget = None  # type: QtWidgets.QListWidgetItem
        self.image_size = 180
        self.thumbnail_margin = 20

        if pose_asset.thumbnail_data:
            icon = QtGui.QIcon()
            qimg = QtGui.QImage.fromData(pose_asset.thumbnail_data)
            pixmap = QtGui.QPixmap.fromImage(qimg)
            icon.addPixmap(pixmap)
            self.setIcon(icon)

        self.update_size(self.image_size)

        self.value_display_overlay = ValueDisplayOverlay(self)
        self.value_display_overlay.setVisible(False)

    def mousePressEvent(self, event):
        if event.buttons() == QtCore.Qt.MidButton:
            self.start_blending.emit(self.pose_asset)
        else:
            self.apply_pose.emit(self.pose_asset)
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
        self.image_size = size
        self.setMinimumWidth(self.image_size)
        self.setMinimumHeight(self.image_size)
        self.setIconSize(QtCore.QSize(self.image_size - self.thumbnail_margin, self.image_size - self.thumbnail_margin))

        if self.list_widget_item and self.list_widget_widget:
            self.list_widget_item.setSizeHint(self.list_widget_widget.sizeHint())


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

        self.pose_grid = QtWidgets.QListWidget()
        self.pose_grid.setViewMode(QtWidgets.QListWidget.IconMode)
        self.pose_grid.setResizeMode(QtWidgets.QListWidget.Adjust)
        self.pose_grid.setLayoutMode(QtWidgets.QListWidget.Batched)

        self.rig_chooser = QtWidgets.QComboBox()

        main_layout = QtWidgets.QVBoxLayout()
        main_layout.setSpacing(2)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(self.pose_filter)
        main_layout.addWidget(self.size_slider)
        main_layout.addWidget(self.pose_grid)
        main_layout.addWidget(self.rig_chooser)
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


if __name__ == "__main__":
    main()

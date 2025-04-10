import sys
import argparse
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget,
    QVBoxLayout, QLabel, QPushButton,
    QFileDialog, QTreeWidget, QTreeWidgetItem, QHBoxLayout
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QKeySequence, QIcon, QPixmap, QShortcut
import pydagmc
from pydagmc import DAGModel
import os


class DAGMCViewer(QMainWindow):
    def __init__(self, filename=None):
        super().__init__()
        self.setWindowTitle("DAGMC Model Viewer")
        self.setMinimumSize(800, 600)

        logo_path = os.path.join(os.path.dirname(__file__), "assets", "dagmc_logo.png")
        if os.path.exists(logo_path):
            self.setWindowIcon(QIcon(logo_path))

        self.dag_model = None

        self.init_ui()
        self.init_shortcuts()

        if filename:
            self.load_from_file(filename)

    def init_ui(self):
        main_widget = QWidget()
        main_layout = QVBoxLayout()

        header_layout = QHBoxLayout()
        logo_path = os.path.join(os.path.dirname(__file__), "assets", "dagmc_logo.png")
        if os.path.exists(logo_path):
            logo_label = QLabel()
            logo_pixmap = QPixmap(logo_path).scaledToHeight(32, Qt.SmoothTransformation)
            logo_label.setPixmap(logo_pixmap)
            header_layout.addWidget(logo_label)
        else:
            header_layout.addWidget(QLabel("[Logo not found]"))

        title_label = QLabel("<b>DAGMC Model Viewer</b>")
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        main_layout.addLayout(header_layout)

        button_layout = QHBoxLayout()
        self.load_button = QPushButton("Load .h5m File")
        self.load_button.clicked.connect(self.load_file)
        button_layout.addWidget(self.load_button)

        self.reset_button = QPushButton("Reset")
        self.reset_button.clicked.connect(self.reset_view)
        button_layout.addWidget(self.reset_button)

        main_layout.addLayout(button_layout)

        self.tree_widget = QTreeWidget()
        self.tree_widget.setSelectionMode(QTreeWidget.ExtendedSelection)
        self.tree_widget.setHeaderLabels(["DAGMC Model Entities"])
        self.tree_widget.itemSelectionChanged.connect(self.update_export_button_state)
        main_layout.addWidget(self.tree_widget)

        self.export_button = QPushButton("Export Selection to VTK")
        self.export_button.setEnabled(False)
        self.export_button.clicked.connect(self.export_selected_entities)
        main_layout.addWidget(self.export_button)

        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)

    def init_shortcuts(self):
        QShortcut(QKeySequence("Ctrl+Q"), self, activated=self.close)
        QShortcut(QKeySequence("Ctrl+W"), self, activated=self.close)
        QShortcut(QKeySequence("Ctrl+C"), self, activated=self.close)

    def load_file(self):
        file_dialog = QFileDialog(self)
        file_dialog.setNameFilter("DAGMC Files (*.h5m)")
        if file_dialog.exec():
            file_name = file_dialog.selectedFiles()[0]
            self.load_from_file(file_name)

    def load_from_file(self, file_name):
        self.dag_model = DAGModel(file_name)
        self.populate_tree()

    def create_item(self, label, entity):
        item = QTreeWidgetItem([label])
        item.setData(0, Qt.UserRole, entity)
        return item

    def populate_tree(self):
        self.tree_widget.clear()

        if self.dag_model is None:
            return

        root_groups = QTreeWidgetItem(["Groups"])
        for group in self.dag_model.groups:
            group_label = f"Group {group.id}: {group.name}"
            group_item = self.create_item(group_label, group)
            for vol in group.volumes:
              vol_item = self.create_item(f"Volume {vol.id}", vol)
              for surf in vol.surfaces:
                  surf_item = self.create_item(f"Surface {surf}", surf)
                  vol_item.addChild(surf_item)
              group_item.addChild(vol_item)
            root_groups.addChild(group_item)

        root_volumes = QTreeWidgetItem(["Volumes"])
        for vol in self.dag_model.volumes:
            vol_item = self.create_item(f"Volume {vol.id}", vol)
            for surf in vol.surfaces:
                vol_item.addChild(self.create_item(f"Surface {surf}", surf))
            root_volumes.addChild(vol_item)

        root_surfaces = QTreeWidgetItem(["Surfaces"])
        for surf in self.dag_model.surfaces:
            surf_item = self.create_item(f"Surface {surf}", surf)
            root_surfaces.addChild(surf_item)

        self.tree_widget.addTopLevelItem(root_groups)
        self.tree_widget.addTopLevelItem(root_volumes)
        self.tree_widget.addTopLevelItem(root_surfaces)
        self.tree_widget.collapseAll()

    def reset_view(self):
        self.dag_model = None
        self.tree_widget.clear()
        self.export_button.setEnabled(False)

    def update_export_button_state(self):
        selected_items = self.tree_widget.selectedItems()
        self.export_button.setEnabled(bool(selected_items))

    def export_selected_entities(self):
        selected_items = self.tree_widget.selectedItems()
        if not selected_items:
            return
        # Placeholder for actual VTK export logic
        selected_sets = [item.data(0, Qt.UserRole) for item in selected_items]
        # surfaces contain the triangles and we only care about writing those
        surfaces_out = []
        for selected_set in selected_sets:
          if isinstance(selected_set, pydagmc.Group):
            surfaces_out += selected_set.surfaces
          if isinstance(selected_set, pydagmc.Volume):
            surfaces_out += selected_set.surfaces
          if isinstance(selected_set, pydagmc.Surface):
            surfaces_out += [selected_set]

        # collect handles and ensure they are unique
        output_handles = {s.handle for s in surfaces_out}
        file_dialog = QFileDialog(self)
        file_dialog.setAcceptMode(QFileDialog.AcceptSave)
        file_dialog.setNameFilter("VTK Files (*.vtk)")
        file_dialog.setDefaultSuffix("vtk")
        if file_dialog.exec():
            output_path = file_dialog.selectedFiles()[0]
            self.dag_model.mb.write_file(output_path, output_sets=list(output_handles))



def main():
    parser = argparse.ArgumentParser(description="DAGMC Viewer")
    parser.add_argument("filename", nargs="?", help="Path to a .h5m file to open")
    args = parser.parse_args()

    app = QApplication(sys.argv)
    viewer = DAGMCViewer(args.filename)
    viewer.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()

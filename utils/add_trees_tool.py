from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtGui import QCursor, QPixmap, QColor
from qgis.core import QgsWkbTypes, QgsVectorLayer, QgsFeature, QgsPointLocator, QgsProject, QgsGeometry
from qgis.gui import QgsRubberBand, QgsMapToolIdentify
from qgis.utils import iface

from ..gui.add_tree_dialog import AddTreeDialog


class AddTreesTool(QgsMapToolIdentify):
    def __init__(self, parent):
        self.canvas = iface.mapCanvas()
        super(AddTreesTool, self).__init__(self.canvas)

        self.parent = parent
        self.locator = None

        self.temp_point = QgsRubberBand(iface.mapCanvas(), QgsWkbTypes.PointGeometry)
        self.temp_point.setColor(QColor('green'))
        self.temp_point.setIcon(QgsRubberBand.ICON_X)
        self.temp_point.setWidth(3)
        self.temp_point.setIconSize(10)

        self.setCursor(QCursor(QPixmap(["16 16 2 1",
                                        "      c None",
                                        ".     c #000000",
                                        "                ",
                                        "        .       ",
                                        "        .       ",
                                        "      .....     ",
                                        "     .     .    ",
                                        "    .   .   .   ",
                                        "   .    .    .  ",
                                        "   .    .    .  ",
                                        " ... ... ... ...",
                                        "   .    .    .  ",
                                        "   .    .    .  ",
                                        "    .   .   .   ",
                                        "     .     .    ",
                                        "      .....     ",
                                        "        .       ",
                                        "        .       "])))

    def canvasMoveEvent(self, e):
        if self.locator is None:
            return

        tolerance = 3*self.canvas.mapUnitsPerPixel()
        result = self.locator.nearestVertex(e.mapPoint(), tolerance)
        self.temp_point.reset(QgsWkbTypes.PointGeometry)

        if not result.isValid():
            result = self.locator.nearestEdge(e.mapPoint(), tolerance)

        if result.isValid():
            point = QgsGeometry.fromPointXY(result.point())
            self.temp_point.addGeometry(point)

    def canvasReleaseEvent(self, e):
        if not self.soil_layer:
            return

        self.set_locator()

        if e.button() == Qt.LeftButton:
            results = self.identify_soil(e, self.soil_layer)
            if not results:
                return
            feature = results[0].mFeature
            self.open_add_new_feature_dialog(e.mapPoint(), feature)
            self.temp_point.reset(QgsWkbTypes.PointGeometry)

    def open_add_new_feature_dialog(self, point, feature: QgsFeature):
        result = 0
        while result == 0:
            dialog = AddTreeDialog(
                [point], feature[self.soil_field_name], self.trees_layer)
            dialog.fill_data()
            result = dialog.exec()

    def set_layers(self, trees_layer: QgsVectorLayer, soil_layer: QgsVectorLayer, roads_layer: QgsVectorLayer):
        self.trees_layer = trees_layer
        self.soil_layer = soil_layer
        self.roads_layer = roads_layer
        self.set_locator()

    def set_soil_field(self, field_name: str):
        self.soil_field_name = field_name

    def identify_soil(self, e, layer):
        results = self.identify(e.x(), e.y(), [layer])
        return results

    def set_locator(self):
        if self.roads_layer is not None:
            self.locator = QgsPointLocator(
                self.roads_layer,
                self.canvas.mapSettings().destinationCrs(),
                QgsProject.instance().transformContext())
        else:
            self.locator = None

    def deactivate(self):
        super(AddTreesTool, self).deactivate()
        self.temp_point.reset(QgsWkbTypes.PointGeometry)
        # self.locator = None
        # self.trees_layer = None
        # self.soil_layer = None
        # self.roads_layer = None

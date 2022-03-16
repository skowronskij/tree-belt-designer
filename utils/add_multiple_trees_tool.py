from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtGui import QCursor, QPixmap, QColor
from qgis.core import QgsWkbTypes, QgsVectorLayer, QgsFeature, QgsPointLocator, QgsProject, QgsFeatureRequest
from qgis.gui import QgsRubberBand, QgsMapToolIdentify
from qgis.utils import iface

from ..gui.add_tree_dialog import AddTreeDialog


class AddMultipleTreesTool(QgsMapToolIdentify):
    def __init__(self, parent):
        self.canvas = iface.mapCanvas()
        super(AddMultipleTreesTool, self).__init__(self.canvas)

        self.parent = parent
        self.locator = None

        self.temp_line = QgsRubberBand(
            iface.mapCanvas(), QgsWkbTypes.LineGeometry)
        self.temp_line.setColor(QColor('red'))
        self.temp_line.setWidth(1)
        self.temp_line.setLineStyle(Qt.DotLine)

        self.final_line = QgsRubberBand(
            iface.mapCanvas(), QgsWkbTypes.LineGeometry)
        self.final_line.setColor(QColor('red'))
        self.final_line.setWidth(1)

        self.snapping_point = QgsRubberBand(
            iface.mapCanvas(), QgsWkbTypes.PointGeometry)
        self.snapping_point.setColor(QColor('green'))
        self.snapping_point.setIcon(QgsRubberBand.ICON_X)
        self.snapping_point.setWidth(3)
        self.snapping_point.setIconSize(10)

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
        self.temp_line.movePoint(e.snapPoint())
        self.snapping_point.reset(QgsWkbTypes.PointGeometry)

        if not result.isValid():
            result = self.locator.nearestEdge(e.mapPoint(), tolerance)

        if result.isValid():
            self.snapping_point.addPoint(e.snapPoint())

    def canvasReleaseEvent(self, e):
        if not self.soil_layer:
            return

        self.set_locator()

        if e.button() == Qt.LeftButton:
            # results = self.identify_soil(e, self.soil_layer)
            # if not results:
            #     return
            # feature = results[0].mFeature
            self.final_line.addPoint(e.snapPoint())
            self.temp_line.addPoint(e.snapPoint())
        elif e.button() == Qt.RightButton:
            self.identify_soil()
            self.final_line.reset(QgsWkbTypes.LineGeometry)
            self.temp_line.reset(QgsWkbTypes.LineGeometry)
            # self.open_add_new_feature_dialog(e.mapPoint(), feature)

    def open_add_new_feature_dialog(self, points, feature: QgsFeature):
        result = 0
        while result == 0:
            dialog = AddTreeDialog(
                points, feature[self.soil_field_name], self.trees_layer, self.final_line.asGeometry())
            dialog.fill_data()
            result = dialog.exec()

    def set_layers(self, trees_layer: QgsVectorLayer, soil_layer: QgsVectorLayer, roads_layer: QgsVectorLayer):
        self.trees_layer = trees_layer
        self.soil_layer = soil_layer
        self.roads_layer = roads_layer
        self.set_locator()

    def set_soil_field(self, field_name: str):
        self.soil_field_name = field_name

    def identify_soil(self):
        feature_request = QgsFeatureRequest(
            self.final_line.asGeometry().boundingBox())

        for f in self.soil_layer.getFeatures(feature_request):
            self.open_add_new_feature_dialog([], f)

    def set_locator(self):
        if self.roads_layer is not None:
            self.locator = QgsPointLocator(
                self.roads_layer,
                self.canvas.mapSettings().destinationCrs(),
                QgsProject.instance().transformContext())
        else:
            self.locator = None

    def deactivate(self):
        super(AddMultipleTreesTool, self).deactivate()
        self.final_line.reset(QgsWkbTypes.LineGeometry)
        self.temp_line.reset(QgsWkbTypes.LineGeometry)
        self.locator = None
        self.trees_layer = None
        self.soil_layer = None
        self.roads_layer = None

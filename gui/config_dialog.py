import os

from typing import List
from qgis.PyQt import uic
from qgis.PyQt.QtWidgets import QDialog, QRadioButton, QDialogButtonBox
from qgis.core import QgsMapLayerProxyModel, QgsVectorLayer, QgsProject, Qgis
from qgis.gui import QgsMapLayerComboBox
from qgis.utils import iface

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'config_dialog.ui'))

FIELDS = [
    {'name': 'species_name', 'type': 'string'},
    {'name': 'height', 'type': 'integer'},
    {'name': 'width', 'type': 'integer'}
]

SOIL_LAYER_RECLASS_REQUIRED_FIELDS = ['Hab_1', 'Hab_2', 'Hab_3']


class ConfigDialog(QDialog, FORM_CLASS):
    def __init__(self, tools: List, parent=None):
        super(ConfigDialog, self).__init__(parent)
        self.setupUi(self)

        self.tools = tools
        self.__init_config()

    def __init_config(self) -> None:
        """ Connecting signals, filters, type-hinting config etc. """
        self.mlCbSoil: QgsMapLayerComboBox
        self.mlCbPoints: QgsMapLayerComboBox
        self.mlCbRoads: QgsMapLayerComboBox

        self.rbNewLayer: QRadioButton

        self.buttonBox: QDialogButtonBox

        self.mlCbSoil.setFilters(QgsMapLayerProxyModel.PolygonLayer)
        self.mlCbPoints.setFilters(QgsMapLayerProxyModel.PointLayer)
        self.mlCbRoads.setFilters(QgsMapLayerProxyModel.LineLayer)

        self.__connect_signals()

    def __connect_signals(self):
        self.buttonBox.accepted.connect(self._setup_tools)
        self.rbNewLayer.toggled.connect(self._menage_point_layer_input)
        self.cbxTypeField.toggled.connect(self._toggle_field_selection)

    def _setup_tools(self):

        if self.rbNewLayer.isChecked():
            point_layer = self._create_layer()
        else:
            point_layer = self.mlCbPoints.currentLayer()

        for tool in self.tools:
            tool.set_soil_field(self._get_soil_field())
            tool.set_layers(point_layer, self.mlCbSoil.currentLayer(),
                            self.mlCbRoads.currentLayer())

    def _get_soil_field(self):
        if self.cbxTypeField.isChecked():
            return self.flCbSoilField.currentField()
        else:
            return 'TYP'

    def _toggle_field_selection(self, toggled: bool) -> None:
        self.flCbSoilField.setEnabled(toggled)

        if not toggled:
            self.flCbSoilField.setLayer(None)
        else:
            if not self.flCbSoilField.layer():
                self.flCbSoilField.setLayer(self.mlCbSoil.currentLayer())

    def layers_valid(self, message=False) -> bool:
        soil_layer = self.mlCbSoil.currentLayer()
        if not soil_layer:
            if message:
                iface.messageBar().pushMessage('Tree Belt Designer',
                                               'Soil layer not provided', Qgis.Critical, 4)
            return False

        field_names = soil_layer.fields().names()
        for required_field in SOIL_LAYER_RECLASS_REQUIRED_FIELDS:
            if required_field not in field_names:
                if message:
                    iface.messageBar().pushMessage('Tree Belt Designer',
                                                   'Layer was not reclassified', Qgis.Critical, 4)
                return False

        if not self.mlCbRoads.currentLayer():
            if message:
                iface.messageBar().pushMessage('Tree Belt Designer',
                                               'Linear arrangement layer not provided', Qgis.Critical, 4)
            return False

        return True

    def _menage_point_layer_input(self, state: bool):
        self.mlCbPoints.setEnabled(not state)
        self.lblPoints.setEnabled(not state)
        self.layerName.setEnabled(state)

    def _create_layer(self) -> QgsVectorLayer:
        epsg = self.mlCbSoil.currentLayer().sourceCrs()
        fields = 'field=%s' % '&field='.join(
            ['%s:%s' % (f['name'], f['type']) for f in FIELDS])
        layer_name = self.layerName.text() or 'trees'
        new_layer = QgsVectorLayer(f'Point?{fields}', layer_name, 'memory')
        new_layer.setCrs(epsg)
        new_layer.reload()
        QgsProject.instance().addMapLayer(new_layer, True)
        new_layer.setCustomProperty('cm_trees_layer', True)
        return new_layer

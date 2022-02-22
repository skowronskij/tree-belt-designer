import os
import sqlite3
from PyQt5.QtWidgets import QLabel

from qgis.PyQt import uic
from qgis.PyQt.QtWidgets import QDialog, QComboBox, QDialogButtonBox, QLineEdit
from qgis.core import QgsVectorLayer, QgsFeature, QgsPointXY, QgsGeometry, Qgis
from qgis.utils import iface

from ..db.db_handler import db_handler
from .select_species_dialog import SelectSpeciesDialog

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'add_single_tree_dialog.ui'))


class AddSinglePointDialog(QDialog, FORM_CLASS):
    def __init__(self, point: QgsPointXY, soil_type: str, layer: QgsVectorLayer, parent=None):
        super(AddSinglePointDialog, self).__init__(parent)
        self.setupUi(self)

        self.point = point
        self.soil_type = soil_type
        self.trees_layer = layer
        self.species_result = None

        self.__init_config()

    def __init_config(self) -> None:
        """ Connecting signals, filters, type-hinting config etc. """
        # Type-hinting for linter
        self.lblSoilType: QLabel
        self.lblSoilType.setText(f'Soil type: {self.soil_type}')
        self.cbTreeOptimum: QComboBox
        self.cbTreeMedium: QComboBox
        self.cbTreeLow: QComboBox

        self.leHeight: QLineEdit
        self.leWidth: QLineEdit

        self.buttonBox: QDialogButtonBox

        self.__connect_singals()

    def __connect_singals(self):
        pass
        self.buttonBox.accepted.connect(self._pass_data)
        # self.cbTreeOptimum.currentTextChanged.connect(self._fill_add_data)

    def fill_data(self):
        try:
            items = zip([self.cbTreeOptimum, self.cbTreeMedium,
                        self.cbTreeLow], ['optimum', 'medium', 'low'])
            for cbTrees, category in items:
                trees = db_handler.select_species_by_soil_type(
                    self.soil_type, f'soil_type_{category}')
                if not trees:
                    trees.append('No trees or schrubs available')
                else:
                    trees.append('')
                cbTrees.addItems(trees)
        except sqlite3.OperationalError:
            return

    def _fill_add_data(self, text: str):
        current_data = [row for row in self.data if row['name'] == text][0]
        self.leHeight.setText(str(current_data['height']))
        self.leWidth.setText(str(current_data['width']))

    def _gather_trees_names(self):
        comboboxes = {'Optimum': self.cbTreeOptimum,
                      'Medium': self.cbTreeMedium, 'Low': self.cbTreeLow}
        return [{'name': cb.currentText(), 'type': type} for type, cb in comboboxes.items()
                if cb.currentText() or cb.currentText() != 'No trees or schrubs available']

    def _pass_data(self):
        names = self._gather_trees_names()
        if not names:
            iface.messageBar().pushMessage('Tree Belt Designer',
                                           'No data for selected feature', Qgis.Critical, 4)
            return
        select_species_dialog = SelectSpeciesDialog(names, self.soil_type)
        self.species_result, info = select_species_dialog.exec()
        if self.species_result == 1:
            self._add_feature(*info)

    def _add_feature(self, species: str, height: int, width: int):
        if not species:
            iface.messageBar().pushMessage('Tree Belt Designer',
                                           'No data for selected feature', Qgis.Critical, 4)
            return
        f = QgsFeature(self.trees_layer.fields())
        f.setGeometry(QgsGeometry.fromPointXY(self.point))
        f.setAttributes([species, height, width])
        self.trees_layer.dataProvider().addFeatures([f])
        self.trees_layer.triggerRepaint()

    def exec(self) -> int:
        result = super().exec()
        return self.species_result

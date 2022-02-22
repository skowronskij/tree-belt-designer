import os
from PyQt5.QtWidgets import QLayout, QRadioButton

from qgis.PyQt import uic
from qgis.PyQt.QtWidgets import QDialog, QRadioButton

from ..db.db_handler import db_handler

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'select_species_dialog.ui'))

class SelectSpeciesDialog(QDialog, FORM_CLASS):
    def __init__(self, trees: list, soil_type: str, parent=None):
        super(SelectSpeciesDialog, self).__init__(parent)
        self.setupUi(self)
        self.trees = trees
        self.trees_data = self._get_trees_info(self.trees)
        self.lblSoilType.setText(f'Soil type: {soil_type}')
        self.pbLayout: QLayout
        self._create_radio_buttons()

    def _create_radio_buttons(self):
        for info in self.trees_data:
            trees_info_string = '{}\nSpecies: {}\nHeight: {}\nWidth: {}\nShape: {}\nInsolation level: {}\nHabitat: {}\nSoil moisture level: {}' \
            .format(info['type'], info['name'], info['height'], info['width'], info['shape'],
                    info['insolation_level'], info['habitat'], info['soil_moisture_level'])
            rb = QRadioButton(trees_info_string, self)
            self.pbLayout.addWidget(rb)

    def _get_selected_radio_button(self):
        for chbx in self.findChildren(QRadioButton):
            if chbx.isChecked():
                return chbx

    def _get_tree_type(self, name: str):
        for tree in self.trees:
            if tree['name'] == name:
                return tree['type']

    def _get_trees_info(self, trees: list):
        trees_names = tuple([tree['name'] for tree in trees])
        rows = db_handler.select_species_info(trees_names)

        trees_data = []

        for row in rows:
            tree_type = self._get_tree_type(row[0])

            if tree_type == 'Optimum':
                order = 0
            elif tree_type == 'Medium':
                order = 1
            else:
                order = 2

            trees_data.append({
                'name': row[0],
                'height': row[1],
                'width': row[2],
                'shape': row[3],
                'insolation_level': row[4],
                'habitat': row[5],
                'soil_moisture_level': row[6],
                'type': tree_type,
                'order': order
            })

        return sorted(trees_data, key=lambda x: x['order'])

    def _parse_radio_button_data(self, rb: QRadioButton):
        text = rb.text()
        data = text.split('\n')
        name = data[1]
        height = int(data[2].replace('Height: ', ''))
        width = int(data[3].replace('Width: ', ''))
        return name, height, width

    def exec(self) -> int:
        result = super().exec()
        selected_radio_button = self._get_selected_radio_button()
        if not selected_radio_button:
            return 0, None
        return result, self._parse_radio_button_data(selected_radio_button)
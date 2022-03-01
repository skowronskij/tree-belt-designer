import os
import ntpath
import tempfile

from qgis.PyQt import uic
from qgis.PyQt.QtWidgets import QDialog
from qgis.core import QgsMapLayerProxyModel, QgsVectorLayer, QgsFeature, QgsProject, QgsRasterLayer, Qgis
from qgis.gui import QgsMapLayerComboBox, QgsFileWidget
from qgis.analysis import QgsRasterCalculatorEntry, QgsRasterCalculator
from qgis import processing
from qgis.utils import iface

# This loads your .ui file so that PyQt can populate your plugin with the elements from Qt Designer
FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'raster_maker_dialog.ui'))


REQUIRED_FIELDS = [
    'species_name',
    'height',
    'width',
]


class RasterMakerDialog(QDialog, FORM_CLASS):
    def __init__(self, parent=None):
        """Constructor."""
        super(RasterMakerDialog, self).__init__(parent)
        self.setupUi(self)

        self.__init_config()

    def __init_config(self):
        self.mlCbDem: QgsMapLayerComboBox
        self.mlcbTreeOptimums: QgsMapLayerComboBox
        self.fwFilePath: QgsFileWidget

        self.mlCbDem.setFilters(QgsMapLayerProxyModel.RasterLayer)
        self.mlcbTreeOptimums.setFilters(QgsMapLayerProxyModel.PointLayer)
        self.fwFilePath.setStorageMode(QgsFileWidget.SaveFile)

    def create_raster(self):
        dem_layer = self.mlCbDem.currentLayer()
        if not dem_layer:
            iface.messageBar().pushMessage('Tree Belt Designer',
                                           'DEM layer not provided', Qgis.Critical, 4)
            return

        path = self.fwFilePath.filePath()
        if not path:
            iface.messageBar().pushMessage('Tree Belt Designer',
                                           f'Save path not provided', Qgis.Critical, 4)
            return

        # bin_buffer_layer = self._create_buffer_raster(binary=True)
        # self.calculate_raster(bin_buffer_layer, dem_layer, '"dem@1" * "ras@1"', path)
        # new_dem = QgsRasterLayer(path, 'new_dem')

        buffer_layer = self._create_buffer_raster()
        if not buffer_layer:
            return
        res = self.calculate_raster(
            buffer_layer, dem_layer, '"dem@1" + "ras@1"', path)
        if res != QgsRasterCalculator.Success:
            iface.messageBar().pushMessage('Tree Belt Designer',
                                           f'Raster generate error: {res}', Qgis.Critical, 4)
            return

        filename = ntpath.basename(path)
        QgsProject.instance().removeMapLayers([buffer_layer.id()])
        # HOTFIX: na widnows, do innego fixu później
        try:
            os.remove(self.tmp_filename)
        except PermissionError:
            pass
        QgsProject.instance().addMapLayer(QgsRasterLayer(path, filename))

    def calculate_raster(self, layer: QgsRasterLayer, dem_layer: QgsRasterLayer, query: str, path: str):
        ras = QgsRasterCalculatorEntry()
        ras.ref = 'ras@1'
        ras.raster = layer
        ras.bandNumber = 1

        dem = QgsRasterCalculatorEntry()
        dem.ref = 'dem@1'
        dem.raster = dem_layer
        dem.bandNumber = 1

        entries = [ras, dem]
        calc = QgsRasterCalculator(query, path, 'GTiff', dem_layer.extent(
        ), dem_layer.width(), dem_layer.height(), entries)
        return calc.processCalculation()

    def _create_buffer_layer(self) -> QgsVectorLayer:
        trees_layer = self.mlcbTreeOptimums.currentLayer()
        if not trees_layer:
            return
        if not self._validate_trees_layer(trees_layer):
            return
        epsg = trees_layer.sourceCrs()
        new_layer = QgsVectorLayer(
            f'Polygon?field=height:double(20,5)', 'trees_buffer', 'memory')
        new_layer.setCrs(epsg)
        feats = []
        for f in trees_layer.getFeatures():
            buffer_geom = f.geometry().buffer(f['width'], 100)
            new_f = QgsFeature(new_layer.fields())
            new_f.setGeometry(buffer_geom)
            new_f.setAttributes([f['height']])
            feats.append(new_f)
        features_sorted_by_height = sorted(feats, key=lambda f: f['height'])
        new_layer.dataProvider().addFeatures(features_sorted_by_height)
        new_layer.reload()
        QgsProject.instance().addMapLayer(new_layer, False)
        return new_layer

    def _validate_trees_layer(self, layer: QgsVectorLayer) -> bool:
        for field in REQUIRED_FIELDS:
            if field not in layer.fields().names():
                iface.messageBar().pushMessage('Tree Belt Designer',
                                               'Required fields not found in trees and shrubs layer', Qgis.Critical, 4)
                return False
        return True

    def _create_buffer_raster(self, binary=False) -> QgsVectorLayer:

        def fix_extent(ext: str):
            ext = ext.replace(',', '')
            ext_list = ext.split(' ')
            return f'{ext_list[0]},{ext_list[2]},{ext_list[1]},{ext_list[3]}'

        dem_layer = self.mlCbDem.currentLayer()
        if not dem_layer:
            iface.messageBar().pushMessage('Tree Belt Designer',
                                           'DEM layer not provided', Qgis.Critical, 4)
            return

        buffer_layer = self._create_buffer_layer()
        if not buffer_layer:
            return
        extent = fix_extent(
            dem_layer.extent().asWktCoordinates()) + ' [EPSG:2180]'
        res = processing.run('gdal:rasterize',
                             {'BURN': 0,
                              'DATA_TYPE': 5,
                              'EXTENT': extent,
                              'EXTRA': '',
                              'FIELD': None if binary else 'height',
                              'HEIGHT': dem_layer.height(),
                              'INIT': None,
                              'INPUT': buffer_layer.metadataUri(),
                              'INVERT': False,
                              'NODATA': -9999,
                              'OPTIONS': '',
                              'OUTPUT': 'TEMPORARY_OUTPUT',
                              'UNITS': 0,
                              'WIDTH': dem_layer.width()})
        filled_no_data = self._replace_no_data(res['OUTPUT'])
        QgsProject.instance().removeMapLayers([buffer_layer.id()])
        layer = QgsRasterLayer(
            filled_no_data, 'buffer_raster_bin' if binary else 'buffer_raster')
        layer.setCrs(dem_layer.crs())
        QgsProject.instance().addMapLayer(layer, False)
        return layer

    def _replace_no_data(self, layer_tmp: str) -> str:
        _, self.tmp_filename = tempfile.mkstemp()
        res = processing.run('grass7:r.null',
                             {'-c': False,
                              '-f': False,
                              '-i': False,
                              '-n': False,
                              '-r': False,
                              'GRASS_RASTER_FORMAT_META': '',
                              'GRASS_RASTER_FORMAT_OPT': '',
                              'GRASS_REGION_CELLSIZE_PARAMETER': 0,
                              'GRASS_REGION_PARAMETER': None,
                              'map': layer_tmp,
                              'null': 0,
                              'output': self.tmp_filename,
                              'setnull': ''})
        return res['output']


"""

{ '-c' : False, '-f' : False, '-i' : False, '-n' : False, '-r' : False, 'GRASS_RASTER_FORMAT_META' : '', 'GRASS_RASTER_FORMAT_OPT' : '', 'GRASS_REGION_CELLSIZE_PARAMETER' : 0, 'GRASS_REGION_PARAMETER' : None, 'map' : '/tmp/processing_8995aaa2dcad49b58a3e449c41ad5942/d4001a6696044a2eb808655821e0fbe0/OUTPUT.tif', 'null' : 1, 'output' : 'TEMPORARY_OUTPUT', 'setnull' : '' }

{ 'BURN' : 0, 'DATA_TYPE' : 5, 'EXTENT' : '349178.9017268746,349200.8050334647,470074.69803179876,470223.2857493622 [EPSG:2180]', 'EXTRA' : '', 'FIELD' : 'nmt_wys', 'HEIGHT' : 500, 'INIT' : None, 'INPUT' : 'MultiPolygon?crs=EPSG:2180&field=id:integer(-1,0)&field=nmt_wys:double(20,5)&uid={68c89983-38ca-4b98-8203-187e94cf4ae5}', 'INVERT' : False, 'NODATA' : -9999, 'OPTIONS' : '', 'OUTPUT' : 'TEMPORARY_OUTPUT', 'UNITS' : 0, 'WIDTH' : 500 }

1. Stworzenie warstwy buforów
2. Stworzenie 0/1 bufor raster 
3. Stworzenie wys bufor rater
4. Raster calc dem in * 0/1 bufor
5. Raster calc dem in + wys bufor  

"""

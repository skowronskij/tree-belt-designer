import os.path
import csv

from qgis.PyQt.QtCore import QSettings, QTranslator, QCoreApplication
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction, QToolButton, QMenu, QFileDialog, QInputDialog
from qgis.core import QgsVectorLayer, QgsProject, Qgis

# Initialize Qt resources from file resources.py
from .resources import *
# Import the code for the dialog
from .gui.config_dialog import ConfigDialog
from .gui.raster_maker_dialog import RasterMakerDialog
from .utils.add_trees_tool import AddTreesTool
from .utils.add_multiple_trees_tool import AddMultipleTreesTool
from .db.db_handler import DB_PATH, db_handler


class TreeBeltDesigner:
    """QGIS Plugin Implementation."""

    def __init__(self, iface):
        """Constructor.

        :param iface: An interface instance that will be passed to this class
            which provides the hook by which you can manipulate the QGIS
            application at run time.
        :type iface: QgsInterface
        """
        # Save reference to the QGIS interface
        self.iface = iface
        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)
        # initialize locale
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            'TreeBeltDesigner_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)
            QCoreApplication.installTranslator(self.translator)

        # Declare instance attributes
        self.actions = []
        self.menu = self.tr(u'&Tree Belt Designer')
        self.add_trees_tool = AddTreesTool(self)
        self.add_multiple_trees_tool = AddMultipleTreesTool(self)
        self.config_dialog = ConfigDialog(
            [self.add_trees_tool, self.add_multiple_trees_tool])

    def tr(self, message):
        """Get the translation for a string using Qt translation API.

        We implement this ourselves since we do not inherit QObject.

        :param message: String for translation.
        :type message: str, QString

        :returns: Translated version of message.
        :rtype: QString
        """
        # noinspection PyTypeChecker,PyArgumentList,PyCallByClass
        return QCoreApplication.translate('TreeBeltDesigner', message)

    def add_action(
            self,
            icon_path,
            text,
            callback=None,
            enabled_flag=True,
            add_to_menu=True,
            add_to_toolbar=True,
            status_tip=None,
            whats_this=None,
            checkable=False,
            parent=None):
        """Add a toolbar icon to the toolbar.

        :param icon_path: Path to the icon for this action. Can be a resource
            path (e.g. ':/plugins/foo/bar.png') or a normal file system path.
        :type icon_path: str

        :param text: Text that should be shown in menu items for this action.
        :type text: str

        :param callback: Function to be called when the action is triggered.
        :type callback: function

        :param enabled_flag: A flag indicating if the action should be enabled
            by default. Defaults to True.
        :type enabled_flag: bool

        :param add_to_menu: Flag indicating whether the action should also
            be added to the menu. Defaults to True.
        :type add_to_menu: bool

        :param add_to_toolbar: Flag indicating whether the action should also
            be added to the toolbar. Defaults to True.
        :type add_to_toolbar: bool

        :param status_tip: Optional text to show in a popup when mouse pointer
            hovers over the action.
        :type status_tip: str

        :param parent: Parent widget for the new action. Defaults None.
        :type parent: QWidget

        :param whats_this: Optional text to show in the status bar when the
            mouse pointer hovers over the action.

        :returns: The action that was created. Note that the action is also
            added to self.actions list.
        :rtype: QAction
        """

        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        if callback:
            action.triggered.connect(callback)
        action.setEnabled(enabled_flag)

        if status_tip is not None:
            action.setStatusTip(status_tip)

        if whats_this is not None:
            action.setWhatsThis(whats_this)

        if add_to_toolbar:
            # Adds plugin icon to Plugins toolbar
            self.iface.addToolBarIcon(action)

        if add_to_menu:
            self.iface.addPluginToMenu(
                self.menu,
                action)

        if checkable:
            action.setCheckable(True)

        self.actions.append(action)

        return action

    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI. MANDATORY METHOD"""

        self.add_trees_menu = self.add_action(
            ':/plugins/potential_isolation_designer/icons/tree_add.png',
            text=self.tr(u'Tree belt designer'),
            parent=self.iface.mainWindow()
        )
        self.set_add_trees_menu()

        self.add_make_raster = self.add_action(
            ':/plugins/potential_isolation_designer/icons/tree_raster.png',
            text=self.tr(u'Potential DSM designer'),
            callback=self.turn_raster_maker,
            parent=self.iface.mainWindow())
        self.make_raster_dialog = RasterMakerDialog()

        self.trees_registry = self.add_action(
            ':/plugins/potential_isolation_designer/icons/tree_registry.png',
            text=self.tr(u'Tree and shrub library designer'),
            parent=self.iface.mainWindow())
        self.set_trees_registry_menu()

    def set_add_trees_menu(self):

        self.add_trees_button = self.iface.pluginToolBar().widgetForAction(self.add_trees_menu)
        self.add_trees_button.setPopupMode(QToolButton.InstantPopup)
        self.add_trees_button.setMenu(QMenu())

        add_trees_menu = self.add_trees_button.menu()

        add_trees_config_action = add_trees_menu.addAction(
            'Tree belt designer - settings')
        add_trees_config_action.triggered.connect(self.config_dialog.exec)

        add_trees_action = self.add_action(
            ':/plugins/potential_isolation_designer/icons/tree_add.png',
            text=self.tr(u'Tree belt designer - add single object'),
            callback=self.turn_add_trees_tool,
            checkable=True,
            parent=self.iface.mainWindow(),
            add_to_menu=False,
            add_to_toolbar=False)
        add_trees_menu.addAction(add_trees_action)
        self.add_trees_tool.setAction(add_trees_action)

        add_multiple_trees_action = self.add_action(
            ':/plugins/potential_isolation_designer/icons/tree_add.png',
            text=self.tr(u'Tree belt designer - add multiple objects'),
            callback=self.turn_add_multiple_trees_tool,
            checkable=True,
            parent=self.iface.mainWindow(),
            add_to_menu=False,
            add_to_toolbar=False)

        add_trees_menu.addAction(add_multiple_trees_action)
        self.add_multiple_trees_tool.setAction(add_multiple_trees_action)

    def set_trees_registry_menu(self):
        self.trees_registry_button = self.iface.pluginToolBar(
        ).widgetForAction(self.trees_registry)
        self.trees_registry_button.setPopupMode(QToolButton.InstantPopup)
        self.trees_registry_button.setMenu(QMenu())

        trees_registry_menu = self.trees_registry_button.menu()

        open_registry_menu = trees_registry_menu.addAction(
            'Edit tree and shrub library'
        )
        open_registry_menu.triggered.connect(self.turn_trees_register)

        update_registry_action = trees_registry_menu.addAction(
            'Update tree and shrub library from csv'
        )
        update_registry_action.triggered.connect(
            self.update_trees_registry_from_csv
        )

        download_registry_action = trees_registry_menu.addAction(
            'Download the structure of tree and shrub library'
        )
        download_registry_action.triggered.connect(self.download_db_structure)

    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        for action in self.actions:
            self.iface.removePluginMenu(
                self.tr(u'&Tree Belt Designer'),
                action)
            self.iface.removeToolBarIcon(action)

    def turn_trees_register(self):
        registry = QgsVectorLayer(DB_PATH, 'trees_registry')
        QgsProject.instance().addMapLayer(registry, False)
        self.iface.showAttributeTable(registry)

    def turn_add_trees_tool(self, toggled: bool):
        if toggled:
            self.iface.mapCanvas().setMapTool(self.add_trees_tool)
        else:
            self.iface.mapCanvas().unsetMapTool(self.add_trees_tool)

    def turn_add_multiple_trees_tool(self, toggled: bool):
        if toggled:
            self.iface.mapCanvas().setMapTool(self.add_multiple_trees_tool)
        else:
            self.iface.mapCanvas().unsetMapTool(self.add_multiple_trees_tool)

    def turn_raster_maker(self, toggled: bool):
        result = self.make_raster_dialog.exec()
        if result != 1:
            return
        self.make_raster_dialog.create_raster()

    def update_trees_registry_from_csv(self):
        ext = 'csv'
        file_path, _ = QFileDialog.getOpenFileName(filter=f'*.{ext}')

        if not file_path:
            return

        delimiter = self.open_delimiter_dialog()

        if not delimiter:
            return

        with open(file_path, 'r') as file:
            reader = csv.reader(file, delimiter=delimiter)
            new_data = [row for row in reader if row and row[0]
                        != 'species_native_name']

        if new_data:
            db_handler.insert_new_rows(new_data)
            self.iface.messageBar().pushMessage('Tree Belt Designer',
                                    'Data added successfuly', Qgis.Success, 4)
        else:
            self.iface.messageBar().pushMessage('Tree Belt Designer',
                                                'No data found in csv', Qgis.Warning, 4)

    def download_db_structure(self):
        ext = 'csv'
        file_path, _ = QFileDialog.getSaveFileName(filter=f'*.{ext}')

        if not file_path:
            return

        full_data = db_handler.get_all_data()

        delimiter = self.open_delimiter_dialog()

        if not delimiter:
            return

        with open(file_path, 'w') as file:
            writer = csv.writer(file, delimiter=delimiter)
            writer.writerow(['species_native_name', 'species_latin_name', 'target_height',
                            'target_width', 'shape', 'soil_type_optimum', 'soil_type_medium',
                             'soil_type_low', 'habitat', 'insolation_level', 'soil_moisture_level'])
            writer.writerows(full_data)

    def open_delimiter_dialog(self):
        delimiter, ok = QInputDialog.getText(
            None, 'Chose delimiter', 'CSV Delimiter:', text=',')
        if ok:
            return delimiter

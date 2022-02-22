# -*- coding: utf-8 -*-
"""
/***************************************************************************
 TreeBeltDesigner
                                 A QGIS plugin
 _placeholder
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                             -------------------
        begin                : 2020-10-03
        copyright            : (C) 2020 by Jakub Skowroński
        email                : skowronski.jakub97@gmail.com
        git sha              : $Format:%H$
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
 This script initializes the plugin, making it known to QGIS.
"""


# noinspection PyPep8Naming
def classFactory(iface):  # pylint: disable=invalid-name
    """Load TreeBeltDesigner class from file TreeBeltDesigner.

    :param iface: A QGIS interface instance.
    :type iface: QgsInterface
    """
    #
    from .tree_belt_designer import TreeBeltDesigner
    return TreeBeltDesigner(iface)

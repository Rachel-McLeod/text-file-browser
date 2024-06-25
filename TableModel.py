import sys
from PyQt5 import QtCore

import DatabaseInterface
import const


class TableModel(QtCore.QAbstractTableModel):
    ''' Model to gather data from an SQL database, expecting a title, body of
        text, and categorised tags '''
    def __init__(self, table=None, parent=None):
        super().__init__(parent)
        self.table = table or const.TABLE
        self._headers = DatabaseInterface.getHeaderNames(self.table)
        self.filterString = ''

    def refreshData(self):
        ''' Refreshes the model data '''
        self.beginResetModel()
        self.endResetModel()

    def rowCount(self, parent=QtCore.QModelIndex()):
        return DatabaseInterface.getEntryCount(self.table, self.filterString)

    def columnCount(self, parent=QtCore.QModelIndex()):
        return len(self._headers)

    def data(self, index, role=QtCore.Qt.DisplayRole):
        if not index.isValid():
            return None
        row = index.row()
        col = index.column()
        if role == QtCore.Qt.DisplayRole:
            if col > len(self._headers) -1:
                return None
            column = self._headers[col]
            return DatabaseInterface.getDataFromRow(column, row, self.table, self.filterString)
        return None

    def headerData(self, section, orientation, role=QtCore.Qt.DisplayRole):
        if orientation == QtCore.Qt.Horizontal and role == QtCore.Qt.DisplayRole:
            return str(self._headers[section])
        return None

    def setFilterString(self, string):
        ''' Sets the filter string '''
        self.filterString = string

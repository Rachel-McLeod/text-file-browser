from PyQt5 import QtWidgets, QtCore

import Utils
import TableModel
import DatabaseInterface


class TagWidget(QtWidgets.QWidget):
    ''' Widget to display an enterd tag, and its deletion'''
    def __init__(self, tag):
        '''
        tag (str): the text for the entered tag
        '''
        super(TagWidget, self).__init__()
        self.text = tag
        self._buildUI()

    def _buildUI(self):
        ''' create the widget UI '''
        # Create the layout
        self.mainLayout = QtWidgets.QHBoxLayout()
        self.label = QtWidgets.QLabel(self.text)
        self.mainLayout.addWidget(self.label)
        self.mainLayout.addStretch()

        # Create delete button
        self.deleteButton = QtWidgets.QPushButton('×')
        self.deleteButton.setFixedSize(20, 20)
        self.mainLayout.addWidget(self.deleteButton)
        self.delete = self.deleteButton.pressed

        # Set the central widget of the main window
        self.mainLayout.setContentsMargins(0,0,0,0)
        self.setLayout(self.mainLayout)

class TextInput(QtWidgets.QWidget):
    ''' Widget for a line edit, and name label '''
    def __init__(self, name):
        '''
        name (str): label for the text box
        '''
        super(TextInput, self).__init__()
        layout = QtWidgets.QVBoxLayout()
        label = QtWidgets.QLabel(name)
        self.textField = QtWidgets.QLineEdit()
        layout.addWidget(label)
        layout.addWidget(self.textField)
        layout.setContentsMargins(0,0,0,0)
        self.setLayout(layout)

        self.editingFinished = self.textField.editingFinished

    def text(self):
        return self.textField.text()

    def setText(self, text):
        self.textField.setText(text)


class TagCategoryWidget(QtWidgets.QWidget):
    ''' widget to allow tag input '''
    # TODO: add the option to read tags and categories directly from the database
    tagsEdited = QtCore.pyqtSignal()
    def __init__(self, categoryName=None, labelName=None, potentialTags=[]):
        super(TagCategoryWidget, self).__init__()

        # get filepath
        config = Utils.Config()
        self.filepath = config.META_FILEPATH
        if not self.filepath:
            Utils.ErrorMessage()
            return

        self.name = categoryName
        self.labelName = labelName or categoryName
        self.potentialTags = potentialTags
        self.appliedTags = []
        self.tagWidgets = []
        self.findTags()
        self._buildUI()


    def _buildUI(self):
        # Create layout
        self.mainLayout = QtWidgets.QVBoxLayout()

        #add separator
        line = QtWidgets.QFrame()
        line.setFrameShape(QtWidgets.QFrame.HLine)
        line.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.mainLayout.addWidget(line)

        # add label
        self.label = QtWidgets.QLabel(self.labelName)
        self.mainLayout.addWidget(self.label)

        # add a layout to add the entered tags to later
        self.tagLayout = QtWidgets.QVBoxLayout()
        self.mainLayout.addLayout(self.tagLayout)

        # add text edit, with a completer for the existing tags
        self.tagInput = QtWidgets.QLineEdit()
        self.mainLayout.addWidget(self.tagInput)
        self.tagInput.editingFinished.connect(self.tagEntered)
        self.completer = QtWidgets.QCompleter(self.potentialTags, self)
        self.completer.setCaseSensitivity(QtCore.Qt.CaseInsensitive)
        self.tagInput.setCompleter(self.completer)

        # Set the central widget of the main window
        self.mainLayout.setContentsMargins(0,0,0,0)
        self.mainLayout.addStretch(2)
        self.setLayout(self.mainLayout)

    def getAppliedTags(self):
        ''' gets the list of tags that have been entered

            returns:
                list: the entered tags
        '''
        return self.appliedTags

    def tagEntered(self):
        ''' Handles a new tag being added '''
        text = self.tagInput.text()
        if text in self.appliedTags or text == '':
            return
        self.appliedTags.append(text)
        widget = TagWidget(text)
        self.tagLayout.addWidget(widget)
        self.tagWidgets.append(widget)

        #connect the new tag's delete to the widget's delete handling method
        widget.delete.connect(lambda: self.deleteTag(widget))

        # Clear the text input when the tag is added
        QtCore.QTimer.singleShot(0, self.tagInput.clear)

        self.tagsEdited.emit()


    def deleteTag(self, tagWidget):
        ''' Handles tag deletion '''
        self.appliedTags.remove(tagWidget.text)
        self.tagLayout.removeWidget(tagWidget)
        tagWidget.setParent(None)
        tagWidget.deleteLater()
        del(tagWidget)
        tagWidget = None
        self.tagsEdited.emit()

    def findTags(self):
        ''' reads the json file and gathers the relevant potential tags, either
        those in the named category or all tags '''
        categories = Utils.getCategories()
        # if no category name is given, get the tags from all categories
        if self.name:
            self.potentialTags = categories.get(self.name)
        else:
            for tags in categories.values():
                self.potentialTags += tags


class NewEntryWidget(QtWidgets.QDialog):
    ''' Widget to create a new database entry, including adding tags '''
    def __init__(self, parent=None):
        super(NewEntryWidget, self).__init__(parent)
        self._buildUI()

    def _buildUI(self):
        self.layout = QtWidgets.QVBoxLayout()
        self.setLayout(self.layout)

        # Add Title and Body text inputs
        self.titleText = TextInput('Title')
        self.layout.addWidget(self.titleText)
        self.bodyText = TextInput('Text Body')
        self.layout.addWidget(self.bodyText)

        # Add TagCategoryWidgets
        self.tagInputs = {}
        self.categories = Utils.getCategories()
        for category, tags in self.categories.items():
            self.tagInputs[category] = TagCategoryWidget(categoryName=category,
                                                         potentialTags=tags)
            self.layout.addWidget(self.tagInputs[category])

        # Add Save button
        self.saveBtn = QtWidgets.QPushButton('Save')
        self.saveBtn.released.connect(self.saveEntry)
        self.saveBtn.setDefault(False)
        self.saveBtn.setAutoDefault(False)
        self.layout.addWidget(self.saveBtn)


    def saveEntry(self):
        ''' Save the entered data as a new database entry '''
        titleText = self.titleText.text()
        bodyText = self.bodyText.text()
        if not (titleText and bodyText):
            Utils.ErrorMessage("Nothing entered for title or text body")
            return

        # Make the new entry to the main table and get its ID
        entryID = DatabaseInterface.addEntry(title=titleText, textBody=bodyText)
        if not entryID:
            Utils.ErrorMessage("Error executing query:" + query.lastError().text())
            self.reject()

        # Add the relevant tags to the various tables to keep track of them
        tagDict = self.getTagDict()
        DatabaseInterface.addTags(entryID, tagDict)
        self.accept()

    def getTagDict(self):
        ''' Find the applied tags for each category and return them as a dictionary
        returns:
            dict of {str: list of str}: the tags organised into categories
        '''
        dict = {}
        for catName, tagWidget in self.tagInputs.items():
            dict[catName] = tagWidget.getAppliedTags()
        return dict


class SearchWidget(QtWidgets.QWidget):
    ''' Widget containing inputs to search and filter the entries shown '''
    def __init__(self, model):
        '''
        Args:
            model (TableModel.TableModel): model with SQL functionality
        '''
        super(SearchWidget, self).__init__()
        self.model = model
        self._buildUI()
        self.filterString = ''

    def _buildUI(self):
        searchBox = QtWidgets.QGroupBox('Search and Filter')
        searchLayout = QtWidgets.QVBoxLayout()
        searchBox.setLayout(searchLayout)

        self.titleSearchText = TextInput("Search Title")
        searchLayout.addWidget(self.titleSearchText)
        self.titleSearchText.editingFinished.connect(self.search)

        self.bodySearchText = TextInput("Search Text")
        searchLayout.addWidget(self.bodySearchText)
        self.bodySearchText.editingFinished.connect(self.search)

        self.tagSearch = TagCategoryWidget(labelName="Filter by tags")
        self.tagSearch.tagsEdited.connect(self.search)
        searchLayout.addWidget(self.tagSearch)

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(searchBox)
        self.setLayout(layout)

    def search(self):
        ''' Update the search results '''
        self.refreshFilterString()
        self.model.setFilterString(self.filterString)
        self.model.refreshData()

    def refreshFilterString(self):
        ''' Makes a filter query string out of the given filters '''
        # Get the current search paramenters
        titleString = self.titleSearchText.text()
        bodyString = self.bodySearchText.text()
        tags = self.tagSearch.getAppliedTags()

        if not titleString and not bodyString and not tags:
            self.filterString =  ''
            return

        # Handle text search for title and body text
        string = ' WHERE '
        if titleString:
            string += 'Title LIKE ' + '"%' + titleString + '%"'
        if bodyString:
            if string.endswith('"'):
                string += ' AND'
            if string[-1] != ' ':
                string += ' '
            string += 'TextBody LIKE ' + '"%' + bodyString + '%"'

        # Find the IDs of the tags to filter by
        indexes = set()
        categoryDict = Utils.getCategories()
        for category, valueTags in categoryDict.items():
            for searchTag in tags:
                if searchTag in valueTags:
                    index = DatabaseInterface.getEntryIDsWithTag(category, searchTag)
                    if not index:
                        continue
                    indexes.update(index)

        # Make a string of the tag IDs
        indexString = ''
        for index in indexes:
            indexString += ' ID={} OR'.format(index)

        # Add strings together for tag IDs and cleanup
        if indexString:
            if string.endswith('"'):
                string += ' AND'
            if indexString.endswith(' OR'):
                indexString = indexString[:-3]
            string += '(' + indexString + ')'

        self.filterString = string



class ReaderWidget(QtWidgets.QMainWindow):
    ''' Displays the search and filter options and shows the resulting entries '''
    def __init__(self):
        super(ReaderWidget, self).__init__()

        # Setup dialog to confirm the file locations for the database
        # and metadata
        setupDialog = Setup()
        if not setupDialog.exec():
            return
        config = Utils.Config()
        self.database = config.DATABASE
        self._buildUI()


    def _buildUI(self):

        mainLayout = QtWidgets.QHBoxLayout()

        # Set the model for the entries
        self.model = TableModel.TableModel()

        # Create the new entry button
        leftMenuLayout = QtWidgets.QVBoxLayout()
        mainLayout.addLayout(leftMenuLayout)
        self.addEntryBtn = QtWidgets.QPushButton('New Entry')
        self.addEntryBtn.released.connect(self.openNewEntryDialog)
        leftMenuLayout.addWidget(self.addEntryBtn)

        # create the search and filter widget
        searchWidget = SearchWidget(self.model)
        leftMenuLayout.addWidget(searchWidget)

        # create the list view to display the search results
        # TODO: show more information by upgrading to a table view
        self.titleListWidget = QtWidgets.QListView()
        self.titleListWidget.setModel(self.model)
        self.titleListWidget.setModelColumn(1)

        mainLayout.addWidget(self.titleListWidget)
        self.titleListWidget.clicked.connect(self.showEntry)

        # Create text browser to show the entry
        self.textDisplay = QtWidgets.QTextBrowser()
        mainLayout.addWidget(self.textDisplay)

        # Set the central widget of the main window
        centralWidget = QtWidgets.QWidget()
        centralWidget.setLayout(mainLayout)
        self.setCentralWidget(centralWidget)

    def openNewEntryDialog(self):
        ''' Show the dialog for creating a new entry '''
        dialog = NewEntryWidget(self)
        dialog.exec_()

    def showEntry(self):
        ''' Shows the text body in the right hand pane '''
        # get the selected index
        titleItem = self.titleListWidget.selectionModel().selectedIndexes()
        if not titleItem:
            return None

        # get the associated text
        title = titleItem[0].data(QtCore.Qt.DisplayRole)
        text = DatabaseInterface.getTextBodyFromTitle(title)
        self.textDisplay.setPlainText(text)

class Setup(QtWidgets.QDialog):
    ''' Dialog to allow the user to specify database and metainfo files '''
    def __init__(self):
        super(Setup, self).__init__()
        self._buildUI()

    def _buildUI(self):
        self.layout = QtWidgets.QVBoxLayout()
        self.setLayout(self.layout)

        self.databaseText = TextInput('Database filepath')
        self.layout.addWidget(self.databaseText)
        self.metaText = TextInput('Database Metainfo filepath')
        self.layout.addWidget(self.metaText)

        self.okBtn = QtWidgets.QPushButton('OK')
        self.okBtn.released.connect(self.save)
        self.layout.addWidget(self.okBtn)

        self.databaseText.setText('DocDB.sqlite')
        self.metaText.setText('TESTstructure')

    def save(self):
        ''' Save the specified filepaths using the Config singleton '''
        config = Utils.Config()
        config.DATABASE_FILEPATH = self.databaseText.text()
        config.META_FILEPATH = self.metaText.text()
        config.DATABASE =  DatabaseInterface.initDatabase(self.databaseText.text())

        if not Utils.validateMetaJson(self.metaText.text()):
            self.reject()

        if not DatabaseInterface.checkDatabase(config.DATABASE):
            self.reject()

        if not DatabaseInterface.checkTableExists():
            self.reject()

        self.accept()

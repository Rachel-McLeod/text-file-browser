import sys
from PyQt5 import QtWidgets

import json
import const

class Config:
    ''' Singleton to store data set at the beginning of the application '''
    _instance = None
    DATABASE_FILEPATH = ''
    META_FILEPATH = ''
    DATABASE = ''

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(Config, cls).__new__(cls, *args, **kwargs)
        return cls._instance

class ErrorMessage(QtWidgets.QMessageBox):
    ''' Simple error message '''
    def __init__(self, message, critical=False):
        super(ErrorMessage, self).__init__()
        self.setIcon(QtWidgets.QMessageBox.Critical)
        self.setText(message)
        self.setWindowTitle("Error")
        print(message)
        self.exec_()
        if critical:
            sys.exit(1)


def getCategories(file=None):
    ''' returns the categories and associated potential tags from the meta file
        args:
            file (str): the filepath for the meta info
        returns:
            dict of {str:[str]}: the dictionary of categories and tags
    '''
    if file is None:
        config = Config()
        file = config.META_FILEPATH

    dict = getJsonData(file)
    return dict.get("categories")

def getCategoryTags(category, file=None):
    ''' gets the tags associated with a given category from the meta file
        args:
            category (str): the category name
            file (str): the filepath for the meta info
        returns:
            list: the tags for the specified category
    '''
    return getCategories(file).get(category)

def getJsonData(file=None):
    ''' returns the complete data from the meta file
        args:
            file (str): the filepath for the meta info
        returns:
            dict: the dictionary from the full json file
    '''
    file = getMetaFile(file)
    if not file.endswith('.json'):
        file+= '.json'
    with open(file) as file:
        data = file.read()
        dict = json.loads(data)
    return dict

def validateMetaJson(file=None):
    ''' validates the meta file, checking its contents are as expected
        args:
            file (str): the filepath for the meta info
        returns:
            bool: if the necessary data structure was found
    '''
    file = getMetaFile(file)
    main = const.MAIN
    data = getJsonData(file)
    categories = data.get(const.CATEGORIES)
    if not categories and data.get(main):
        return False
    if not isinstance(categories, dict) and isinstance(data.get(main), dict):
        return False
    if not isinstance(list(categories.values())[0], list) or isinstance(list(categories.values())[0], set):
        return False
    return True

def getMetaFile(file=None):
    ''' returns a filepath, using the config meta info filepath. Takes an
        optional filepath arg for neat one line checks 
        args:
            file (str): the filepath for the meta info
        returns:
            str: the filepath
    '''
    if file:
        return file
    config = Config()
    return config.META_FILEPATH

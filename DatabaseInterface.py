from PyQt5.QtSql import QSqlDatabase, QSqlQuery

import Utils
import const


def addTags(docID, tagDict):
    ''' Adds the dictionary of given tags to the specified entry ID
        args:
            docID (int): the database ID for the entry
            tagDict (dict of {str: list[str]}): category to tag list dictionary
    '''
    if docID is None:
        Utils.ErrorMessage("No ID found to insert tags")
        return None
    for category, tagList in tagDict.items():
        for tag in tagList:
            tagID = getTagID(category, tag)
            if tagID is None:
                query = QSqlQuery()
                query.prepare(f"INSERT INTO {category + const.INDEXSUFFIX} (Name) VALUES (?)")
                query.addBindValue(tag)
                query.exec()
                tagID = query.lastInsertId()
            query = QSqlQuery()
            query.prepare(f"INSERT INTO {category + const.MAPSUFFIX} ({const.DOCID}, {const.TAGID}) VALUES (?, ?)")
            query.addBindValue(docID)
            query.addBindValue(tagID)
            query.exec()

def getTagID(category, tag):
    ''' Get a tag's ID from a category and tag name
        args:
            category (str): category name
            tag (str): tag name
        returns:
            int: the tag's ID
    '''
    query = QSqlQuery(f"SELECT TagID FROM {category + const.INDEXSUFFIX} WHERE TagName='{tag}'")
    if query.next():
        return query.value(0)
    return None

def getEntryIDsWithTag(category, tag):
    ''' Get a list of entry IDs that are associated with a given tag
        args:
            category (str): category name
            tag (str/int): tag name or ID
        returns:
            list: the entry IDs that match the given tag
    '''
    # Check if the tag argument is a name or ID, and find the ID if necessary
    if isinstance(tag, str):
        tag = getTagID(category, tag)
        if tag is None:
            return []
    query = QSqlQuery(f"SELECT {const.DOCID} FROM {category + const.MAPSUFFIX} WHERE {const.TAGID} = '{tag}'")
    indexes = []
    while query.next():
        indexes.append(query.value(0))
    return indexes

def addEntry(title=None, textBody=None):
    ''' Create a new database entry from a given title and text body
        args:
            title (str): title
            textBody (str): textBody
        returns:
            int: the ID of the new entry
    '''
    query = QSqlQuery()
    query.prepare("INSERT INTO Docs ({}, {}) VALUES (?, ?)".format(const.TITLE, const.TEXT))
    query.addBindValue(title)
    query.addBindValue(textBody)

    if not query.exec():
        Utils.ErrorMessage("Error executing query:" + query.lastError().text())
        return None
    return query.lastInsertId()


def initDatabase(file):
    ''' Initialise a database from a given file
        args:
            file (str): filepath for the database
        returns:
            PyQt5.QtSql.QSqlDatabase: the initialised database
    '''
    database = QSqlDatabase.addDatabase('QSQLITE')
    if not file.endswith('.sqlite'):
        file = file + '.sqlite'
    database.setDatabaseName(file)

    if not database.open():
        Utils.ErrorMessage("Error: Could not open database.", critical=True)

    return database

def getTextBodyFromTitle(title):
    ''' Searches the database for a given title and returns the matching text
        args:
            title (str): the title to search for
        returns:
            str: the body text and title
    '''
    query = QSqlQuery(f"SELECT {const.TITLE}, {const.TEXT} FROM {const.TABLE} WHERE {const.TITLE} = '{title}'")
    if query.next():
        title = query.value(0)
        text_body = query.value(1)
    query.finish()
    return f"Title: {title}\n\n{text_body}"

def getHeaderNames(table=const.TABLE):
    ''' Finds the main table's headings
        args:
            table (str): the table to search
        returns:
            list of str: the table headings
    '''
    headers = []
    query = QSqlQuery()
    query.exec("SELECT * FROM {}".format(table))

    # Get the number of columns in the query result
    if query.next():
        record = query.record()
        num_columns = record.count()

        # Get each name
        for i in range(num_columns):
            column_name = record.fieldName(i)
            headers.append(column_name)

    return headers

def getEntryCount(table=const.TABLE, filter=''):
    ''' Finds the number of entries, allowing for filtering
        args:
            table (str): the table to search
            filter (str): additions to the query specifying seach str or filters
        returns:
            int: the number of rows found
    '''
    query = QSqlQuery()
    query.exec("SELECT COUNT(*) FROM  {}{}".format(table, filter))

    if(query.first()):
        rows = query.value(0);
        return rows
    return -1

def getDataFromRow(column, row, table=const.TABLE, filter=''):
    ''' Finds the data held in the database's specified row and column
        args:
            column (int): the table column
            row (int): the table row
            table (str): the table to search
            filter (str): additions to the query specifying seach str or filters
        returns:
            int/str: the data found
    '''
    query = QSqlQuery()
    queryString = 'SELECT {} FROM {} {}'.format(column, table, filter)
    query.exec(queryString)
    query.seek(row)
    return query.value(0)

def checkTableExists(table=const.TABLE):
    ''' Checks if a table exists
        args:
            table (str): the table to search for
        returns:
            bool: whether the table exists
    '''
    query = QSqlQuery("IF EXISTS(SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = '{}')".format(table))
    return query == "found"

def checkDatabase(database=None):
    ''' Checks if a database exists/ can be opened
        args:
            database (PyQt5.QtSql.QSqlDatabase): the database
        returns:
            bool: whether the database exists
    '''
    if not database:
        config = Utils.Config()
        database = config.DATABASE

    if not database.open():
        ErrorMessage("Error: Could not open database.")
        return False
    return True

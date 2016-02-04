import re

import xlrd

from .utils import is_number


class Parser(object):
    """
    This superclass models the various parsers that will retrieve and store the data
    and implements their common functions.
    """

    def __init__(self, log, config, area_repo=None, indicator_repo=None, observation_repo=None):
        self._log = log
        self._config = config
        self._indicator_repo = indicator_repo
        self._area_repo = area_repo
        self._observation_repo = observation_repo

    @property
    def indicator_repo(self):
        return self._indicator_repo

    @property
    def area_repo(self):
        return self._area_repo

    @property
    def observation_repo(self):
        return self._observation_repo

    @staticmethod
    def _get_sheet(file_name, sheet_name_or_index):
        """
        Retrieves a xlrd sheet object given its file name and its index within it.
        :param file_name:
        :param sheet_number:
        :return xlrd sheet object:
        """
        book = xlrd.open_workbook(file_name)
        sheet = book.sheet_by_index(sheet_name_or_index) if is_number(sheet_name_or_index) else book.sheet_by_name(
            sheet_name_or_index)
        return sheet

    @staticmethod
    def _get_sheets_by_pattern(file_name, regex_pattern):
        pattern = re.compile(regex_pattern)
        book = xlrd.open_workbook(file_name)
        matching_sheet_names = [sheet_name for sheet_name in book.sheet_names() if pattern.match(sheet_name)]
        matching_sheets = [book.sheet_by_name(sheet_name) for sheet_name in matching_sheet_names]
        return matching_sheets


class ParserError(Exception):
    """
    Exception parent class for all parsers, this class could be subclassed for custom behaviour

    Attributes:
        message (str): Error message for this exception
    """

    def __init__(self, message, custom_header=""):
        """
        Constructor for ParserError

        Args:
            message (str): Error message for this exception
            custom_header (str): Title to introduce the error message
        """
        self._message = message
        self._custom_header = custom_header

    @property
    def message(self):
        return self._custom_header + " " + self._message

import xlrd
# from infrastructure.mongo_repos.indicator_repository import IndicatorRepository
# from infrastructure.mongo_repos.observation_repository import ObservationRepository
# from infrastructure.mongo_repos.area_repository import AreaRepository
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

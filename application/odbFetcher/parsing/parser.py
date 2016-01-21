import xlrd
# from infrastructure.mongo_repos.indicator_repository import IndicatorRepository
from infrastructure.sql_repos.indicator_repository import IndicatorRepository
# from infrastructure.mongo_repos.observation_repository import ObservationRepository
# from infrastructure.mongo_repos.area_repository import AreaRepository
from .utils import is_number

__author__ = 'Rodrigo'


class Parser(object):
    """
    This superclass models the various parsers that will retrieve and store the data
    and implements their common functions.
    """

    def __init__(self, log, config):
        self._log = log
        self._config = config
        self._indicator_repo, self._observation_repo, self._area_repo = self._initialize_repositories()

    def _initialize_repositories(self):
        """
        Initializes the database repositories that will be used by every parser to store the data.
        :return indicator_repo, observation_repo, area_repo:
        """
        # indicator_repo = IndicatorRepository(self._config.get("CONNECTION", "MONGO_IP"))
        indicator_repo = IndicatorRepository(self._log)
        observation_repo = None  # ObservationRepository(self._config.get("CONNECTION", "MONGO_IP"))
        area_repo = None  # AreaRepository(self._config.get("CONNECTION", "MONGO_IP"))
        return indicator_repo, observation_repo, area_repo

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

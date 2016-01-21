from odb.domain.model.indicator.indicator import *
from odb.domain.model.observation.observation import *
from odb.domain.model.observation.year import Year

__author__ = 'Rodrigo'

"""
This module provides utility functions to the parsing classes. Among these functions, there are the ones responsible
for transforming the elements retrieved from the Excel files from their auxiliary model classes to the corresponding
domain model classes.
"""


def string_to_bool(string):
    return string in ["True", "true"]


def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        pass

    try:
        import unicodedata
        unicodedata.numeric(s)
        return True
    except (TypeError, ValueError):
        pass

    return False


def excel_indicator_to_dom(excel_indicator):
    indicator = create_indicator(type=excel_indicator.type,
                                 name=excel_indicator.name,
                                 indicator=excel_indicator.code,
                                 republish=excel_indicator.republishable,
                                 description=excel_indicator.name,
                                 provider_name=excel_indicator.provider_name,
                                 provider_url=excel_indicator.provider_url)
    return indicator


def excel_observation_to_dom(excel_observation, area, indicator):
    observation = create_observation(value=excel_observation.value,
                                     republish=indicator.republish,
                                     area=area.iso3,
                                     area_name=area.name,
                                     indicator=indicator.indicator,
                                     indicator_name=indicator.name,
                                     provider_name=indicator.provider_name,
                                     provider_url=indicator.provider_url,
                                     short_name=area.short_name,
                                     year=Year(2014),
                                     continent=area.area)
    return observation

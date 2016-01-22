from __future__ import division

import re

from odb.domain.model.indicator.indicator import *
from odb.domain.model.observation.observation import *
from odb.domain.model.observation.year import Year

__author__ = 'Rodrigo'

"""
This module provides utility functions to the parsing classes. Among these functions, there are the ones responsible
for transforming the elements retrieved from the Excel files from their auxiliary model classes to the corresponding
domain model classes.
"""

is_fraction_pattern = re.compile(ur'^\d+(\.\d*)?(/\d+(\.\d*)?)?$')


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


def weight_to_float(s):
    if s is not None and is_fraction_pattern.match(s):
        try:
            return eval(s)
        except ZeroDivisionError:
            pass

    return None


def excel_indicator_to_dom(excel_indicator):
    indicator = create_indicator(index=excel_indicator.index_code,
                                 type=excel_indicator.type,
                                 name=excel_indicator.name,
                                 indicator=excel_indicator.code,
                                 description=excel_indicator.description,
                                 provider_name=excel_indicator.provider_name,
                                 component=excel_indicator.component_code,
                                 source_name=excel_indicator.source_name,
                                 subindex=excel_indicator.subindex_code,
                                 tags=excel_indicator.tags,
                                 weight=excel_indicator.weight)
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


if __name__ == "__main__":
    assert weight_to_float('0') == 0
    assert weight_to_float('0.') == 0
    assert weight_to_float('1') == 1
    assert weight_to_float('1/2') == 0.5
    assert weight_to_float('1/3') == 1 / 3
    assert weight_to_float('') is None
    assert weight_to_float(None) is None
    print 'OK!'

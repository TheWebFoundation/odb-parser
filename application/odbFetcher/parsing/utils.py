import re

from odb.domain.model.area.country import create_country
from odb.domain.model.area.region import create_region
from odb.domain.model.indicator.indicator import *
from odb.domain.model.observation.observation import *
from odb.domain.model.observation.year import Year

"""
This module provides utility functions to the parsing classes. Among these functions, there are the ones responsible
for transforming the elements retrieved from the Excel files from their auxiliary model classes to the corresponding
domain model classes.
"""

is_fraction_pattern = re.compile(r'^\d+(\.\d*)?(/\d+(\.\d*)?)?$')


def string_to_bool(string):
    if not string:
        return False
    else:
        return string.lower().strip() == "true"


def is_not_empty(string):
    if not string:
        return False
    else:
        return len(string.lower().strip()) > 0


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


def colx_from_colname(colname):
    colx = 0
    for ch in colname:
        colx = colx * 26 + ord(ch) - ord('A') + 1
    return colx - 1


def get_column_number(colname):
    """

    Args:
        colname (str): a colname that can either be an identifier 'A', 'B', 'AF', etc. or a number '0', '1', '127'

    Returns:
        (int): the column number as an integer ready to be passed to xlrd functions
    """
    return colx_from_colname(colname) if colname.isalpha() else int(colname)


def weight_to_float(s):
    if s is not None and is_fraction_pattern.match(s):
        try:
            return eval(s)
        except ZeroDivisionError:
            pass

    return None


def excel_indicator_to_dom(excel_indicator):
    indicator = create_indicator(component=excel_indicator.component,
                                 description=excel_indicator.description,
                                 format_notes=excel_indicator.format_notes,
                                 index=excel_indicator.index,
                                 indicator=excel_indicator.code,
                                 license=excel_indicator.license,
                                 name=excel_indicator.name,
                                 provider_name=excel_indicator.provider_name,
                                 provider_url=excel_indicator.provider_url,
                                 range=excel_indicator.range,
                                 source_data=excel_indicator.source_data,
                                 source_name=excel_indicator.source_name,
                                 source_url=excel_indicator.source_url,
                                 subindex=excel_indicator.subindex,
                                 tags=excel_indicator.tags,
                                 type=excel_indicator.type,
                                 units=excel_indicator.units,
                                 weight=excel_indicator.weight)
    return indicator


def excel_observation_to_dom(excel_observation, area, indicator):
    observation = create_observation(value=excel_observation.value,
                                     year=Year(excel_observation.year),
                                     scaled=excel_observation.scaled,
                                     rank=excel_observation.rank,
                                     rank_change=excel_observation.rank_change,
                                     indicator=indicator,
                                     area=area)
    return observation


def excel_region_to_dom(excel_region):
    """Transforms an excel region into a domain entity
    Args:
        excel_region (excel_model.ExcelArea): the excel region

    Returns:
        Region

    """
    region = create_region(name=excel_region.name, iso2=excel_region.iso2, iso3=excel_region.iso3,
                           short_name=excel_region.name)
    return region


def excel_country_to_dom(excel_country):
    """Transforms an excel country into a domain entity
    Args:
        excel_country (excel_model.ExcelArea): the excel country

    Returns:
        Country

    """
    country = create_country(name=excel_country.name, iso2=excel_country.iso2, iso3=excel_country.iso3,
                             short_name=excel_country.name, area=excel_country.region, hdi_rank=excel_country.hdi_rank,
                             g20=excel_country.g20, g7=excel_country.g7, iodch=excel_country.iodch,
                             oecd=excel_country.oecd, income=excel_country.income)
    return country


def str_to_none(s):
    if s is not None:
        stripped = s.strip()
        return None if stripped == "" else stripped
    else:
        return s


def na_to_none(s):
    if s is not None:
        stripped = str(s).strip()
        return None if stripped == "" or stripped.lower() == "na" or stripped.lower() == "n/a" else s
    else:
        return s


if __name__ == "__main__":
    assert weight_to_float('0') == 0
    assert weight_to_float('0.') == 0
    assert weight_to_float('1') == 1
    assert weight_to_float('1/2') == 0.5
    assert weight_to_float('1/3') == 1 / 3
    assert weight_to_float('') is None
    assert weight_to_float(None) is None
    print('OK!')

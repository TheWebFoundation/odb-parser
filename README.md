# ODB 2015
## Getting started
1. Clone this repo.
2. Install the requirements with `pip install -r requirements.txt`
3. Download the Excel file with the ODB data, put it under the `application` subfolder with the name `data.xlsx` (the name could be different, but in that case we'll have to change it in the settings)
4. Parse the data with the app under the `application` subfolder
    1. (Optional) Configure the parser settings under `parser_config.ini`
    2. Run the parser: `python parse.py`, the resulting sqlite database will be on the root folder with the name `odb2015.db`
5. Serve the data with the app under the `api` subfolder
    1. Run the server: `python api.py`
6. Generate the jsons with the app under the `application` subfolder
    1. Run the app: `python generate_json_files.py`
    2. Get the results under the `json` subfolder
    
The parser makes use of two files `search.json` and `fake_iso_codes.json` to enrich the data.

- The `fake_iso_codes.json` file is a manually crafted file specifiying iso codes for top level virtual regions
- The `search.json` file is generated with the script listed in the appendix. The file contains semicolon separated names in different languages for iso codes

## `parser_config.ini` description
This file is used to configure how the excel spreadsheet is parsed. The file is divided in different sections which relate to parts of the spreadsheet. Each setting has a key and a value separated by an equal sign (e.g. FILE_NAME = data.xlsx).

### Structure access section
This section holds configuration for parsing the descriptions for the indicators.

- `FILE_NAME` entry holds the name of the spreadsheet file, relative to the `parser_config.ini` file location. *Note* This key is specified in all sections to be future proof and accommodate a use case in which the spreadsheet sheets could be in different files.
- `INDICATOR_SHEET_NUMBER` entry holds the sheet number of the indicators info. It must be a number and it is zero based.
- `INDICATOR_XXXX_COLUMN` entry holds the column specifying the value for a field named XXXX. The value must be either a letter (e.g. A, B, AJ, etc) or a number (e.g. 1,2,3, etc)
- `INDICATOR_START_ROW` entry holds the first row with data. It must be a number and it is zero based (usually the value will be 1, to account for the header row)
- `INDICATOR_SUBINDEX_COMPONENT_SHEET_NUMBER` entry holds the sheet number of the primary, secondary and component indicators. It must be a number and it is zero based.
- `INDICATOR_SUBINDEX_COMPONENT_XXXX_COLUMN` entry holds the column specifying the value for a field named XXXX. The value must be either a letter (e.g. A, B, AJ, etc) or a number (e.g. 1,2,3, etc)
- `INDICATOR_SUBINDEX_COMPONENT_STAR_ROW` entry holds the first row with data. It must be a number and it is zero based (usually the value will be 1, to account for the header row)

### Area access section
This section holds configuration for parsing information about the areas and countries.

- `FILE_NAME` entry holds the name of the spreadsheet file, relative to the `parser_config.ini` file location. *Note* This key is specified in all sections to be future proof and accommodate a use case in which the spreadsheet sheets could be in different files.
- `AREA_SHEET_NUMBER` entry holds the sheet number of the area info. It must be a number and it is zero based.
- `AREA_START_ROW` entry holds the first row with data. It must be a number and it is zero based (usually the value will be 1, to account for the header row)
- `AREA_XXXX_COLUMN` entry holds the column specifying the value for a field named XXXX. The value must be either a letter (e.g. A, B, AJ, etc) or a number (e.g. 1,2,3, etc)

### Raw observations
This section holds configuration for parsing the values for raw observations (those that are not ranked).

- `FILE_NAME` entry holds the name of the spreadsheet file, relative to the `parser_config.ini` file location. *Note* This key is specified in all sections to be future proof and accommodate a use case in which the spreadsheet sheets could be in different files.
- `SHEET_NAME_PATTERN` entry holds a regular expression indicating the names of the sheets with raw observation data. The regular expression must have a capturing group for parsing the year in the sheet's name (e.g. `^ODB-(?P<year>\d+)-Scores$` will match sheets like ODB-2015-Scores or ODB-2014-Scores).
- `OBSERVATION_NAME_ROW` entry holds the row number where the names of the indicators are (usually the first row). It must be a number and it is zero based.
- `OBSERVATION_START_ROW` entry holds the first row with data. It must be a number and it is zero based (usually the value will be 1, to account for the header row)
- `OBSERVATION_CHECK_COLUMN` entry holds the column to check whether to ignore or not a row. If the column indicated is not empty, we assume it had data and we parse the row. The rationale behind this column is that sometimes, after new data was entered, some rows were left with incomplete or derived data (e.g. average values, old rows, etc). Usually those rows had only a few columns filled in the middle of the sheet (where the actual observation data is). This is a simple check to be able to filter out those incomplete rows. The value must be either a letter (e.g. A, B, AJ, etc) or a number (e.g. 1,2,3, etc)
- `OBSERVATION_START_COLUMN` entry holds the column where the observation data starts. Usually the first columns are devoted to information regarding the year or country. The actual scores start after all that columns. *Note* to account for different layouts each year we can append `_YEAR` (e.g. OBSERVATION_START_COLUM_2015) to override the default value.
- `OBSERVATION_YEAR_COLUMN` entry holds the column with the year. The value must be either a letter (e.g. A, B, AJ, etc) or a number (e.g. 1,2,3, etc). *Note* to account for different layouts each year we can append `_YEAR`.
- `OBSERVATION_ISO3_COLUMN` entry holds the column with the country iso3. The value must be either a letter (e.g. A, B, AJ, etc) or a number (e.g. 1,2,3, etc). *Note* to account for different layouts each year we can append `_YEAR`.

### Dataset observations
This section holds configuration for parsing the values for dataset observations.

- `FILE_NAME` entry holds the name of the spreadsheet file, relative to the `parser_config.ini` file location. *Note* This key is specified in all sections to be future proof and accommodate a use case in which the spreadsheet sheets could be in different files.
- `SHEET_NAME_PATTERN` entry holds a regular expression indicating the names of the sheets with raw observation data. The regular expression must have a capturing group for parsing the year in the sheet's name (e.g. `^ODB-(?P<year>\d+)-Datasets-Scored$` will match sheets like ODB-2015-Datasets-Scored or ODB-2014-Datasets-Scored).
- `OBSERVATION_START_COLUMN` entry holds the column where the observation data starts. Usually the first columns are devoted to information regarding the year or country. The actual scores start after all that columns. *Note* to account for different layouts each year we can append `_YEAR` (e.g. OBSERVATION_START_COLUM_2015) to override the default value.
- `OBSERVATION_NAME_ROW` entry holds the row number where the names of the indicators are (usually the first row). It must be a number and it is zero based.
- `OBSERVATION_START_ROW` entry holds the first row with data. It must be a number and it is zero based (usually the value will be 1, to account for the header row)
- `OBSERVATION_YEAR_COLUMN` entry holds the column with the year. The value must be either a letter (e.g. A, B, AJ, etc) or a number (e.g. 1,2,3, etc). *Note* to account for different layouts each year we can append `_YEAR`.
- `OBSERVATION_ISO3_COLUMN` entry holds the column with the country iso3. The value must be either a letter (e.g. A, B, AJ, etc) or a number (e.g. 1,2,3, etc). *Note* to account for different layouts each year we can append `_YEAR`.
- `OBSERVATION_INDICATOR_COLUMN` entry holds the name of the indicator related to this dataset. The value must be either a letter (e.g. A, B, AJ, etc) or a number (e.g. 1,2,3, etc). *Note* to account for different layouts each year we can append `_YEAR`.

### Structure observations
This section holds configuration for parsing the values for raw observations (those that are ranked and relate to index, subindices or components).

- `FILE_NAME` entry holds the name of the spreadsheet file, relative to the `parser_config.ini` file location. *Note* This key is specified in all sections to be future proof and accommodate a use case in which the spreadsheet sheets could be in different files.
- `SHEET_NAME_PATTERN` entry holds a regular expression indicating the names of the sheets with raw observation data. The regular expression must have a capturing group for parsing the year in the sheet's name (e.g. `^ODB-(?P<year>\d+)-Rankings$` will match sheets like ODB-2015-Rankings or ODB-2014-Rankings).
- `OBSERVATION_NAME_ROW` entry holds the row number where the names of the indicators are (usually the first row). It must be a number and it is zero based.
- `OBSERVATION_START_ROW` entry holds the first row with data. It must be a number and it is zero based (usually the value will be 1, to account for the header row)
- `OBSERVATION_CHECK_COLUMN` entry holds the column to check whether to ignore or not a row. If the column indicated is not empty, we assume it had data and we parse the row. The rationale behind this column is that sometimes, after new data was entered, some rows were left with incomplete or derived data (e.g. average values, old rows, etc). Usually those rows had only a few columns filled in the middle of the sheet (where the actual observation data is). This is a simple check to be able to filter out those incomplete rows. The value must be either a letter (e.g. A, B, AJ, etc) or a number (e.g. 1,2,3, etc)
- `OBSERVATION_YEAR_COLUMN` entry holds the column with the year. The value must be either a letter (e.g. A, B, AJ, etc) or a number (e.g. 1,2,3, etc). *Note* to account for different layouts each year we can append `_YEAR`.
- `OBSERVATION_ISO3_COLUMN` entry holds the column with the country iso3. The value must be either a letter (e.g. A, B, AJ, etc) or a number (e.g. 1,2,3, etc). *Note* to account for different layouts each year we can append `_YEAR`.
- `OBSERVATION_INDEX_RANK_COLUMN` entry holds the column with the index score.The value must be either a letter (e.g. A, B, AJ, etc) or a number (e.g. 1,2,3, etc). *Note* to account for different layouts each year we can append `_YEAR`.
- `OBSERVATION_INDEX_CHANGE_COLUMN` entry holds the column with the index rank change. The value must be either a letter (e.g. A, B, AJ, etc) or a number (e.g. 1,2,3, etc). *Note* to account for different layouts each year we can append `_YEAR`.
- `OBSERVATION_INDEX_SCALED_COLUMN` entry holds the column with the index scaled score. The value must be either a letter (e.g. A, B, AJ, etc) or a number (e.g. 1,2,3, etc). *Note* to account for different layouts each year we can append `_YEAR`.
- `OBSERVATION_SUBINDEX_START_COLUMN` entry holds the first column with subindex and component data. The value must be either a letter (e.g. A, B, AJ, etc) or a number (e.g. 1,2,3, etc). *Note* to account for different layouts each year we can append `_YEAR`.
- `OBSERVATION_SUBINDEX_SCALED_COLUMN_PATTERN` entry holds a regular expression to know which subindex corresponds to the values in the column. The regular expression must capture that in the group `subindex` (e.g. `^(?P<subindex>\w+)-scaled$` will parse subindices like `implementation-scaled`). *Note* to account for different layouts each year we can append `_YEAR`.
- `OBSERVATION_SUBINDEX_RANK_COLUMN_PATTERN` entry holds a regular expression to know which subindex corresponds to the rank in the column. The regular expression must capture that in the group `subindex` (e.g. `^(?P<subindex>\w+)-rank$` will parse subindices like `implementation-rank`). *Note* to account for different layouts each year we can append `_YEAR`.
- `OBSERVATION_COMPONENT_SCALED_COLUMN_PATTERN` entry holds a regular expression to know which subindex and component corresponds to the values in the column. The regular expression must capture that in the groups `subindex` and `component` (e.g. `^(?P<subindex>\w+)-(?P<component>\w+)-scaled$` will parse subindices like `Readiness-Business-Scaled`). *Note* to account for different layouts each year we can append `_YEAR`.
- `ALIAS-XXXX-YEAR` entries hold the aliases for some subindices (e.g.  
Government` in 2014 and 2015 was `Action` in 2013) 

### Area info
This section holds configuration for additional information regarding countries (e.g. cluster information).

- `FILE_NAME` entry holds the name of the spreadsheet file, relative to the `parser_config.ini` file location. *Note* This key is specified in all sections to be future proof and accommodate a use case in which the spreadsheet sheets could be in different files.
- `SHEET_NAME_PATTERN` entry holds a regular expression indicating the names of the sheets with area information. The regular expression must have a capturing group for parsing the year in the sheet's name (e.g. `^ODB-(?P<year>\d+)-Rankings$` will match sheets like ODB-2015-Rankings or ODB-2014-Rankings).
- `AREA_INFO_NAME_ROW` entry holds the row number where the names of the indicators are (usually the first row). It must be a number and it is zero based.
- `AREA_INFO_START_ROW` entry holds the first row with data. It must be a number and it is zero based (usually the value will be 1, to account for the header row)
- `AREA_INFO_YEAR_COLUMN` entry holds the column with the year. The value must be either a letter (e.g. A, B, AJ, etc) or a number (e.g. 1,2,3, etc). *Note* to account for different layouts each year we can append `_YEAR`.
- `AREA_INFO_ISO3_COLUMN` entry holds the column with the country iso3. The value must be either a letter (e.g. A, B, AJ, etc) or a number (e.g. 1,2,3, etc). *Note* to account for different layouts each year we can append `_YEAR`.
- `AREA_INFO_CLUSTER_GROUP_COLUMN_PATTERN` entry holds a regular expression to know if a column holds the values for the cluster group of an area. 

### Others
- `HOST` entry holds the url that is appended to the url field of indicators.

*Note* a complete `parser_config.ini` file able to parse the spreadsheet available on 2016-04-15 can be found in the Appendix.  

## Notes
- Based on the code for the A4AI domain model using DDD and Hexagonal Architecture
- Source code comments:
    - **TODO**: Things work well without implementing this change, but it might be a good idea to take it into account in the future
    - **FIXME**: This should be corrected, specially before going into production
    - **HACK**: A hack
    - **XXX**: Custom marker, probably also a **HACK**
    
## FIXME and TODO
- Mainly pydocs 

## Appendix
### `config_parser.ini`
```
# Columns can be specified either by number (0 based) or by name
# Settings can be overridden for an specific year by appending it XXXXX_YEAR

[STRUCTURE_ACCESS]
FILE_NAME = data.xlsx
INDICATOR_SHEET_NUMBER = 1
INDICATOR_SUBINDEX_COLUMN = A
INDICATOR_COMPONENT_COLUMN = B
INDICATOR_CODE_COLUMN = C
INDICATOR_NAME_COLUMN = D
INDICATOR_DESCRIPTION_COLUMN = E
INDICATOR_TAGS_COLUMN = F
INDICATOR_SOURCE_NAME_COLUMN = G
INDICATOR_SOURCE_URL_COLUMN = H
INDICATOR_SOURCE_DATA_COLUMN = I
INDICATOR_PROVIDER_NAME_COLUMN = J
INDICATOR_PROVIDER_URL_COLUMN = K
INDICATOR_LICENSE_COLUMN = L
INDICATOR_TYPE_COLUMN = M
INDICATOR_RANGE_COLUMN = N
INDICATOR_UNITS_COLUMN = O
INDICATOR_FORMAT_NOTES_COLUMN = P
INDICATOR_START_ROW = 1

INDICATOR_SUBINDEX_COMPONENT_SHEET_NUMBER = 0
INDICATOR_SUBINDEX_COMPONENT_START_ROW = 1
INDICATOR_SUBINDEX_COMPONENT_TYPE_COLUMN = A
INDICATOR_SUBINDEX_COMPONENT_CODE_COLUMN = B
INDICATOR_SUBINDEX_COMPONENT_NAME_COLUMN = C
INDICATOR_SUBINDEX_COMPONENT_DESCRIPTION_COLUMN = D
INDICATOR_SUBINDEX_COMPONENT_SHORT_NAME_COLUMN = E
INDICATOR_SUBINDEX_COMPONENT_WEIGHT_COLUMN = F
INDICATOR_SUBINDEX_COMPONENT_SOURCE_NAME_COLUMN = H
INDICATOR_SUBINDEX_COMPONENT_SOURCE_URL_COLUMN = I
INDICATOR_SUBINDEX_COMPONENT_SOURCE_DATA_COLUMN = J
INDICATOR_SUBINDEX_COMPONENT_PROVIDER_NAME_COLUMN = K
INDICATOR_SUBINDEX_COMPONENT_PROVIDER_URL_COLUMN = L
INDICATOR_SUBINDEX_COMPONENT_LICENSE_COLUMN = M
INDICATOR_SUBINDEX_COMPONENT_RANGE_COLUMN = O
INDICATOR_SUBINDEX_COMPONENT_UNITS_COLUMN = P
INDICATOR_SUBINDEX_COMPONENT_FORMAT_NOTES_COLUMN = Q

[AREA_ACCESS]
FILE_NAME = data.xlsx
AREA_SHEET_NUMBER = 2
AREA_START_ROW = 1
AREA_ISO2_COLUMN = A
AREA_ISO3_COLUMN = B
AREA_NAME_COLUMN = C
AREA_REGION_COLUMN = F
AREA_INCOME_COLUMN = J
AREA_HDI_RANK_COLUMN = K
AREA_G20_COLUMN = L
AREA_G7_COLUMN = M
AREA_IODCH_COLUMN = N
AREA_OECD_COLUMN = O

[RAW_OBSERVATIONS]
FILE_NAME = data.xlsx
SHEET_NAME_PATTERN = ^ODB-(?P<year>\d+)-Scores$
OBSERVATION_NAME_ROW = 0
OBSERVATION_START_ROW = 1
# If this column doesn't have a value, we'll skip that row
# This serves to filter rows that have columns with aggregates that were left from some calculation and it is simple
# than having to explicitly put the last row with values
OBSERVATION_CHECK_COLUMN = A
OBSERVATION_START_COLUMN_2015 = F
OBSERVATION_START_COLUMN = E
OBSERVATION_YEAR_COLUMN = A
OBSERVATION_ISO3_COLUMN_2015 = D
OBSERVATION_ISO3_COLUMN = C

[DATASET_OBSERVATIONS]
FILE_NAME = data.xlsx
SHEET_NAME_PATTERN = ^ODB-(?P<year>\d+)-Datasets-Scored$
OBSERVATION_NAME_ROW = 0
OBSERVATION_START_ROW = 1
OBSERVATION_START_COLUMN = H
OBSERVATION_YEAR_COLUMN = A
OBSERVATION_ISO3_COLUMN = C
OBSERVATION_INDICATOR_COLUMN = E

[STRUCTURE_OBSERVATIONS]
FILE_NAME = data.xlsx
SHEET_NAME_PATTERN = ^ODB-(?P<year>\d+)-Rankings$
OBSERVATION_NAME_ROW = 0
OBSERVATION_START_ROW = 1
# If this column doesn't have a value, we'll skip that row
# This serves to filter rows that have columns with aggregates that were left from some calculation and it is simple
# than having to explicitly put the last row with values
OBSERVATION_CHECK_COLUMN = A
OBSERVATION_YEAR_COLUMN = A
OBSERVATION_ISO3_COLUMN = D
OBSERVATION_ISO3_COLUMN_2013 = C
OBSERVATION_INDEX_RANK_COLUMN = E
OBSERVATION_INDEX_RANK_COLUMN_2013 = D
OBSERVATION_INDEX_RANK_CHANGE_COLUMN = I
OBSERVATION_INDEX_RANK_CHANGE_COLUMN_2013 =
OBSERVATION_INDEX_SCALED_COLUMN = G
OBSERVATION_INDEX_SCALED_COLUMN_2013 = F
OBSERVATION_SUBINDEX_START_COLUMN = J
OBSERVATION_SUBINDEX_START_COLUMN_2013 = G
OBSERVATION_INDEX_SCALED_COLUMN_PATTERN = ^(?P<index>\w+)-score-scaled$
OBSERVATION_SUBINDEX_SCALED_COLUMN_PATTERN = ^(?P<subindex>\w+)-scaled$
OBSERVATION_SUBINDEX_RANK_COLUMN_PATTERN = ^(?P<subindex>\w+)-rank$
OBSERVATION_COMPONENT_SCALED_COLUMN_PATTERN = ^(?P<subindex>\w+)-(?P<component>\w+)-scaled$
# Only used for components, maps a column with the name on the left part to an indicator with a short name equal to the right part
ALIAS-GOVERNMENT-2014 = ACTION
ALIAS-GOVERNMENT-2013 = ACTION

[AREA_INFO]
FILE_NAME = data.xlsx
SHEET_NAME_PATTERN = ^ODB-(?P<year>\d+)-Rankings$
AREA_INFO_NAME_ROW = 0
AREA_INFO_START_ROW = 1
AREA_INFO_YEAR_COLUMN = A
AREA_INFO_ISO3_COLUMN = D
AREA_INFO_ISO3_COLUMN_2014 = E
AREA_INFO_ISO3_COLUMN_2013 = C
AREA_INFO_CLUSTER_GROUP_COLUMN_PATTERN = ^cluster(-group)?$

[OTHERS]
HOST = http://data.opendatabarometer.org/api
```

### `search.json` generation script
```
'use strict';

// If enough time, we have a better list at https://github.com/onomojo/i18n-country-translations

var countries = require('world-countries'),
    _ = require('lodash'),
    fs = require('fs'),
    csv = require("fast-csv");

// Parse world-countries (useful as it has names in native languages, e.g. Basque)
var search = _.reduce(countries, function (result, country) {
    var nativeNames = _(country.name.native).map(_.values).flatten().value();
    var translatedNames = _(country.translations).map(_.values).flatten().value();

    result[country.cca3] = _.concat([country.name.common], nativeNames, translatedNames);
    return result;
}, {});

// http://ec2-54-201-183-195.us-west-2.compute.amazonaws.com/cow/
// Add countries of the world to add additional language data not present in world-countries (arabic, chinese, etc)
var iso3 = null;
fs.createReadStream("cow.csv")
    .pipe(csv({headers: true}))
    .on("data", function (data) {
        var trimmed = _.mapKeys(data, function (v, k) {
            return _.trim(k); // Some keys have spaces at the beginning
        });
        // Each country has 20 rows in the dataset, one for each language
        // But the iso3 only is present on the first row, we carry it of not present
        iso3 = trimmed['ISO 3166-1 A3'] || iso3;
        search[iso3] || (search[iso3] = []).push(trimmed['Abbr']);
        search[iso3].push(trimmed['Formal Name']);
    })
    .on("end", function () {
        search = _.mapValues(search, function (names) {
            return _(names).compact().uniq().join(';');
        });
        fs.writeFileSync('search.json', JSON.stringify(search));
    });

```

### Export CSV Files
``` bash
mkdir csv
sqlite3 odb2015.db "SELECT iso3 FROM area WHERE iso3 NOT LIKE ':%'" | while read in; do sqlite3 -header -csv odb2015.db "SELECT observation.area AS 'iso3', area.name AS 'country', trim(observation.indicator || ' ' || COALESCE(observation.dataset_indicator, '')) AS 'Indicator code', indicator.name AS 'Indicator name', indicator.type as 'Indicator type', observation.value AS 'value', observation.year AS 'year' From observation inner join indicator on observation.indicator = indicator.indicator inner join area on observation.area = area.iso3 WHERE observation.area='$in' ORDER BY year DESC" > csv/$in.csv; done
```
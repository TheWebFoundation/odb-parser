# ODB 2015
## Getting started
1. Download the Excel file with the ODB data, put it under the `application` subfolder with the name `data.xlsx` (the name could be different, but in that case we'll have to change it in the settings)
2. Parse the data with the app under the `application` subfolder
    1. (Optional) Configure the parser settings under `parser_config.ini`
    2. Run the parser: `python parse.py`, the resulting sqlite database will be on the root folder with the name `odb2015.db`
3. Serve the data with the app under the `api` subfolder
    1. Run the server: `python api.py`
4. Generate the jsons with the app under the `application` subfolder
    1. Run the app: `python generate_json_files.py`
    2. Get the results under the `json` subfolder
    
The parser makes use of two files `search.json` and `fake_iso_codes.json` to enrich the data.
- The `fake_iso_codes.json` file is a manually crafted file specifiying iso codes for top level virtual regions
- The `search.json` file is generated with the script listed in the appendix. The file contains semicolon separated names in different languages for iso codes


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

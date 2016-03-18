# a4aiDom
A4AI domain model using DDD and Hexagonal Architecture


## Notes

- Some columns missing
- Old importer had hardcoded Year (2014)
- Column disposition is different (primary and secondary index descriptions?)
- Some raw indicators have the year in the column name

## Simple script to get search names
```
'use strict';

// Better list at https://github.com/onomojo/i18n-country-translations
var countries = require('world-countries'),
    _ = require('lodash'),
    fs = require('fs');

var search = _.map(countries, function (country) {
    var nativeNames = _(country.name.native).map(_.values).flatten().value();
    var translatedNames = _(country.translations).map(_.values).flatten().value();
    var values = _.concat([country.name.common], nativeNames, translatedNames);
    return {
        search: _(values).compact().uniq().join(';'),
        iso3: country.cca3
    };
});

fs.writeFileSync('search.json', JSON.stringify(search));
```

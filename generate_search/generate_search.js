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
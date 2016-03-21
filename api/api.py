# #########################################################################################
##                                  INITIALISATIONS                                     ##
##########################################################################################
import statistics
from configparser import RawConfigParser
from json import dumps

from flask import Flask, request, render_template, Response
# import sys
# import os
#
# sys.path.append(os.path.abspath(os.path.dirname(__file__) + '/../../a4aiDom'))
from infrastructure.sql_repos.area_repository import AreaRepository
from infrastructure.sql_repos.indicator_repository import IndicatorRepository
from infrastructure.sql_repos.observation_repository import ObservationRepository
from infrastructure.errors.errors import RepositoryError
from flask.ext.cache import Cache

cache = Cache(config={'CACHE_TYPE': 'simple'})
app = Flask(__name__)
cache.init_app(app)

TIMEOUT = 30  # timeout to clean cache in seconds

sqlite_config = RawConfigParser()
sqlite_config.read("../api_sqlite_config.ini")


##########################################################################################
##                                 JSONP DECORATOR                                      ##
##########################################################################################

def json_response(data, request, status=200):
    json = dumps(data, ensure_ascii=False).encode('utf-8')
    callback = request.args.get('callback', False)
    if callback:
        return Response(str(callback) + '(' + str(json) + ');', mimetype="application/javascript; charset=utf-8")
    return Response(json, mimetype="application/json; charset=utf-8", status=status)


def json_response_ok(request, data):
    data = success(data)
    return json_response(data, request)


def json_response_error(request, data):
    data = error(data)
    return json_response(data, request, status=400)


def json_encoder(request, data):
    # Check first in order to convert to dict
    if isinstance(data, list):
        data = [data_element.to_dict() for data_element in data]
    else:
        data = data.to_dict()

    return json_response_ok(request, data)


def area_json_encoder(request, data):
    if request.args.get('info') == 'false':
        if isinstance(data, list):
            data = [data_element.to_dict_without_info() for data_element in data]
        else:
            data = data.to_dict_without_info()
        return json_response_ok(request, data)
    else:
        return json_encoder(request, data)


##########################################################################################
##                                SUCCESS FUNCTION                                      ##
##########################################################################################

def success(data):
    return {"success": True, "data": data}


##########################################################################################
##                                  ERROR FUNCTION                                      ##
##########################################################################################

def error(data):
    return {"success": False, "error": data}


##########################################################################################
##                                  CACHE FUNCTION                                      ##
##########################################################################################

def make_cache_key(*args, **kwargs):
    path = request.path
    args = str(hash(frozenset(request.args.items())))
    return (path + args).encode('utf-8')


##########################################################################################
##                                        ROOT                                          ##
##########################################################################################

@app.route("/")
def index():
    """API Documentation"""
    return render_template('help.html')


##########################################################################################
##                                       AREAS                                          ##
##########################################################################################

@app.route("/areas")
@cache.cached(timeout=TIMEOUT, key_prefix=make_cache_key)
def list_areas():
    """List all areas (countries and region)"""
    order = request.args.get('orderBy')

    area_repo = AreaRepository(recreate_db=False, config=sqlite_config)
    areas = area_repo.find_areas(order)

    return area_json_encoder(request, areas)


@app.route("/areas/countries")
@cache.cached(timeout=TIMEOUT, key_prefix=make_cache_key)
def list_countries():
    order = request.args.get('orderBy')
    area_repo = AreaRepository(recreate_db=False, config=sqlite_config)
    countries = area_repo.find_countries(order)
    return area_json_encoder(request, countries)


@app.route("/areas/regions")
@cache.cached(timeout=TIMEOUT, key_prefix=make_cache_key)
def list_regions():
    order = request.args.get('orderBy')
    area_repo = AreaRepository(recreate_db=False, config=sqlite_config)
    regions = area_repo.find_regions(order)
    return area_json_encoder(request, regions)


@app.route("/areas/<area_code>")
@cache.cached(timeout=TIMEOUT, key_prefix=make_cache_key)
def show_area(area_code):
    area_repo = AreaRepository(recreate_db=False, config=sqlite_config)
    area = area_repo.find_countries_by_code_or_income(area_code)
    return area_json_encoder(request, area)


# FIXME: Previous request already returns countries
@app.route("/areas/<area_code>/countries")
@cache.cached(timeout=TIMEOUT, key_prefix=make_cache_key)
def show_area_countries(area_code):
    order = request.args.get('orderBy')
    area_repo = AreaRepository(recreate_db=False, config=sqlite_config)
    countries = area_repo.find_countries_by_region_or_income(area_code, order)
    return area_json_encoder(request, countries)


##########################################################################################
##                                     INDICATORS                                       ##
##########################################################################################

@app.route("/indicators")
@cache.cached(timeout=TIMEOUT, key_prefix=make_cache_key)
def list_indicators():
    indicators = IndicatorRepository(recreate_db=False, config=sqlite_config).find_indicators()

    return json_encoder(request, indicators)


@app.route("/indicators/index")
@cache.cached(timeout=TIMEOUT, key_prefix=make_cache_key)
def show_index():
    _index = IndicatorRepository(recreate_db=False, config=sqlite_config).find_indicators_index()
    return json_encoder(request, _index)


@app.route("/indicators/subindices")
@cache.cached(timeout=TIMEOUT, key_prefix=make_cache_key)
def list_subindices():
    subindices = IndicatorRepository(recreate_db=False, config=sqlite_config).find_indicators_sub_indexes()
    return json_encoder(request, subindices)


@app.route("/indicators/primary")
@cache.cached(timeout=TIMEOUT, key_prefix=make_cache_key)
def list_primary():
    primary = IndicatorRepository(recreate_db=False, config=sqlite_config).find_indicators_primary()
    return json_encoder(request, primary)


@app.route("/indicators/secondary")
@cache.cached(timeout=TIMEOUT, key_prefix=make_cache_key)
def list_secondary():
    secondary = IndicatorRepository(recreate_db=False, config=sqlite_config).find_indicators_secondary()
    return json_encoder(request, secondary)


@app.route("/indicators/<indicator_code>")
@cache.cached(timeout=TIMEOUT, key_prefix=make_cache_key)
def show_indicator(indicator_code):
    indicator = IndicatorRepository(recreate_db=False, config=sqlite_config).find_indicator_by_code(indicator_code)
    return json_encoder(request, indicator)


@app.route("/indicators/<indicator_code>/indicators")
@cache.cached(timeout=TIMEOUT, key_prefix=make_cache_key)
def list_indicator_indicators(indicator_code):
    indicator = IndicatorRepository(recreate_db=False, config=sqlite_config).find_indicator_by_code(indicator_code)

    if indicator is None:
        return json_encoder(request, indicator)

    indicators = IndicatorRepository(recreate_db=False, config=sqlite_config).find_indicators_indicators(indicator)
    return json_encoder(request, indicators)


@app.route("/indicators/<indicator_code>/primary")
@cache.cached(timeout=TIMEOUT, key_prefix=make_cache_key)
def list_indicator_primary(indicator_code):
    indicator = IndicatorRepository(recreate_db=False, config=sqlite_config).find_indicator_by_code(indicator_code)

    if indicator is None:
        return json_encoder(request, indicator)

    primary = IndicatorRepository(recreate_db=False, config=sqlite_config).find_indicators_primary(indicator)
    return json_encoder(request, primary)


@app.route("/indicators/<indicator_code>/secondary")
@cache.cached(timeout=TIMEOUT, key_prefix=make_cache_key)
def list_indicator_secondary(indicator_code):
    indicator = IndicatorRepository(recreate_db=False, config=sqlite_config).find_indicator_by_code(indicator_code)

    if indicator is None:
        return json_encoder(request, indicator)

    secondary = IndicatorRepository(recreate_db=False, config=sqlite_config).find_indicators_secondary(indicator)
    return json_encoder(request, secondary)


##########################################################################################
##                                    AREA INFO                                         ##
##########################################################################################
@app.route("/areasInfo")
@cache.cached(timeout=TIMEOUT, key_prefix=make_cache_key)
def areas_info():
    areas_info = AreaRepository(recreate_db=False, config=sqlite_config).get_areas_info()
    return json_encoder(request, areas_info)


##########################################################################################
##                                    OBSERVATIONS                                      ##
##########################################################################################
@app.route("/observations")
@cache.cached(timeout=TIMEOUT, key_prefix=make_cache_key)
def list_observations():
    area_repo = AreaRepository(recreate_db=False, config=sqlite_config)
    indicator_repo = IndicatorRepository(recreate_db=False, config=sqlite_config)
    observation_repo = ObservationRepository(recreate_db=False, area_repo=area_repo, indicator_repo=indicator_repo,
                                             config=sqlite_config)
    observations = observation_repo.find_observations()
    return json_encoder(request, observations)


@app.route("/observations/<indicator_code>")
@cache.cached(timeout=TIMEOUT, key_prefix=make_cache_key)
def list_observations_by_indicator(indicator_code):
    area_repo = AreaRepository(recreate_db=False, config=sqlite_config)
    indicator_repo = IndicatorRepository(recreate_db=False, config=sqlite_config)
    observation_repo = ObservationRepository(recreate_db=False, area_repo=area_repo, indicator_repo=indicator_repo,
                                             config=sqlite_config)
    observations = observation_repo.find_observations(indicator_code)
    return json_encoder(request, observations)


@app.route("/observations/<indicator_code>/<area_code>")
@cache.cached(timeout=TIMEOUT, key_prefix=make_cache_key)
def list_observations_by_indicator_and_country(indicator_code, area_code):
    area_repo = AreaRepository(recreate_db=False, config=sqlite_config)
    indicator_repo = IndicatorRepository(recreate_db=False, config=sqlite_config)
    observation_repo = ObservationRepository(recreate_db=False, area_repo=area_repo, indicator_repo=indicator_repo,
                                             config=sqlite_config)
    observations = observation_repo.find_observations(indicator_code, area_code)
    return json_encoder(request, observations)


@app.route("/observations/<indicator_code>/<area_code>/<year>")
@cache.cached(timeout=TIMEOUT, key_prefix=make_cache_key)
def list_observations_by_indicator_and_country_and_year(indicator_code, area_code, year):
    area_repo = AreaRepository(recreate_db=False, config=sqlite_config)
    indicator_repo = IndicatorRepository(recreate_db=False, config=sqlite_config)
    observation_repo = ObservationRepository(recreate_db=False, area_repo=area_repo, indicator_repo=indicator_repo,
                                             config=sqlite_config)
    observations = observation_repo.find_observations(indicator_code, area_code, year)
    return json_encoder(request, observations)


@app.route("/rawObservations/<indicator_code>/<year>")
@cache.cached(timeout=TIMEOUT, key_prefix=make_cache_key)
def pruned_observations_by_indicator_and_year(indicator_code, year):
    area_repo = AreaRepository(recreate_db=False, config=sqlite_config)
    indicator_repo = IndicatorRepository(recreate_db=False, config=sqlite_config)
    observation_repo = ObservationRepository(recreate_db=False, area_repo=area_repo, indicator_repo=indicator_repo,
                                             config=sqlite_config)
    observations = observation_repo.find_tree_observations(indicator_code, year, 'INDICATOR')
    areas = area_repo.find_countries(order="iso3")

    data = {'year': year, 'areas': {}, 'stats': {}}
    for area in areas:
        data['areas'][area.iso3] = {}
        for obs in [obs for obs in observations if obs.area.iso3 == area.iso3]:
            data['areas'][area.iso3][obs.indicator.indicator] = {
                'value': obs.value,
                'rank': obs.rank,
                'rank_change': obs.rank_change
            }

    for indicator_code in set([o.indicator.indicator for o in observations]):
        per_indicator_obs = [o.value for o in observations if
                             o.indicator.indicator == indicator_code and o.value is not None]
        data['stats'][indicator_code] = {}
        data['stats'][indicator_code]['mean'] = statistics.mean(per_indicator_obs)
        data['stats'][indicator_code]['median'] = statistics.median(per_indicator_obs)

    return json_response_ok(request, data)



##########################################################################################
##                                      STATISTICS                                      ##
##########################################################################################
@app.route("/statistics")
@cache.cached(timeout=TIMEOUT, key_prefix=make_cache_key)
def list_observations_statistics():
    area_repo = AreaRepository(recreate_db=False, config=sqlite_config)
    indicator_repo = IndicatorRepository(recreate_db=False, config=sqlite_config)
    observation_repo = ObservationRepository(recreate_db=False, area_repo=area_repo, indicator_repo=indicator_repo,
                                             config=sqlite_config)
    statistics = observation_repo.find_observations_statistics()
    return json_encoder(request, statistics)


@app.route("/statistics/<indicator_code>")
@cache.cached(timeout=TIMEOUT, key_prefix=make_cache_key)
def list_observations_by_indicator_statistics(indicator_code):
    area_repo = AreaRepository(recreate_db=False, config=sqlite_config)
    indicator_repo = IndicatorRepository(recreate_db=False, config=sqlite_config)
    observation_repo = ObservationRepository(recreate_db=False, area_repo=area_repo, indicator_repo=indicator_repo,
                                             config=sqlite_config)
    statistics = observation_repo.find_observations_statistics(indicator_code)
    return json_encoder(request, statistics)


@app.route("/statistics/<indicator_code>/<area_code>")
@cache.cached(timeout=TIMEOUT, key_prefix=make_cache_key)
def list_observations_by_indicator_and_country_statistics(indicator_code, area_code):
    area_repo = AreaRepository(recreate_db=False, config=sqlite_config)
    indicator_repo = IndicatorRepository(recreate_db=False, config=sqlite_config)
    observation_repo = ObservationRepository(recreate_db=False, area_repo=area_repo, indicator_repo=indicator_repo,
                                             config=sqlite_config)
    statistics = observation_repo.find_observations_statistics(indicator_code, area_code)
    return json_encoder(request, statistics)


@app.route("/statistics/<indicator_code>/<area_code>/<year>")
@cache.cached(timeout=TIMEOUT, key_prefix=make_cache_key)
def list_observations_by_indicator_and_country_and_year_statistics(indicator_code, area_code, year):
    area_repo = AreaRepository(recreate_db=False, config=sqlite_config)
    indicator_repo = IndicatorRepository(recreate_db=False, config=sqlite_config)
    observation_repo = ObservationRepository(recreate_db=False, area_repo=area_repo, indicator_repo=indicator_repo,
                                             config=sqlite_config)
    statistics = observation_repo.find_observations_statistics(indicator_code, area_code, year)
    return json_encoder(request, statistics)


##########################################################################################
##                                   VISUALISATION                                      ##
##########################################################################################
@app.route("/visualisations")
@cache.cached(timeout=TIMEOUT, key_prefix=make_cache_key)
def list_observations_visualisations():
    area_repo = AreaRepository(recreate_db=False, config=sqlite_config)
    indicator_repo = IndicatorRepository(recreate_db=False, config=sqlite_config)
    observation_repo = ObservationRepository(recreate_db=False, area_repo=area_repo, indicator_repo=indicator_repo,
                                             config=sqlite_config)
    visualisation = observation_repo.find_observations_visualisation()
    return json_encoder(request, visualisation)


@app.route("/visualisations/<indicator_code>")
@cache.cached(timeout=TIMEOUT, key_prefix=make_cache_key)
def list_observations_by_indicator_visualisations(indicator_code):
    area_repo = AreaRepository(recreate_db=False, config=sqlite_config)
    indicator_repo = IndicatorRepository(recreate_db=False, config=sqlite_config)
    observation_repo = ObservationRepository(recreate_db=False, area_repo=area_repo, indicator_repo=indicator_repo,
                                             config=sqlite_config)
    visualisation = observation_repo.find_observations_visualisation(indicator_code)
    return json_encoder(request, visualisation)


@app.route("/visualisations/<indicator_code>/<area_code>")
@cache.cached(timeout=TIMEOUT, key_prefix=make_cache_key)
def list_observations_by_indicator_and_country_visualisations(indicator_code, area_code):
    area_repo = AreaRepository(recreate_db=False, config=sqlite_config)
    indicator_repo = IndicatorRepository(recreate_db=False, config=sqlite_config)
    observation_repo = ObservationRepository(recreate_db=False, area_repo=area_repo, indicator_repo=indicator_repo,
                                             config=sqlite_config)
    visualisation = observation_repo.find_observations_visualisation(indicator_code, area_code)
    return json_encoder(request, visualisation)


@app.route("/visualisations/<indicator_code>/<area_code>/<year>")
@cache.cached(timeout=TIMEOUT, key_prefix=make_cache_key)
def list_observations_by_indicator_and_country_and_year_visualisations(indicator_code, area_code, year):
    area_repo = AreaRepository(recreate_db=False, config=sqlite_config)
    indicator_repo = IndicatorRepository(recreate_db=False, config=sqlite_config)
    observation_repo = ObservationRepository(recreate_db=False, area_repo=area_repo, indicator_repo=indicator_repo,
                                             config=sqlite_config)
    visualisation = observation_repo.find_observations_visualisation(indicator_code, area_code, year)
    return json_encoder(request, visualisation)


# FIXME
##########################################################################################
##                             VISUALISATION GROUPED BY AREA                            ##
##########################################################################################
@app.route("/visualisationsGroupedByArea")
@cache.cached(timeout=TIMEOUT, key_prefix=make_cache_key)
def list_observations_visualisations_grouped_by_area():
    area_repo = AreaRepository(recreate_db=False, config=sqlite_config)
    indicator_repo = IndicatorRepository(recreate_db=False, config=sqlite_config)
    observation_repo = ObservationRepository(recreate_db=False, area_repo=area_repo, indicator_repo=indicator_repo,
                                             config=sqlite_config)
    visualisation = observation_repo.find_observations_grouped_by_area_visualisation()
    return json_encoder(request, visualisation)


@app.route("/visualisationsGroupedByArea/<indicator_code>")
@cache.cached(timeout=TIMEOUT, key_prefix=make_cache_key)
def list_observations_by_indicator_visualisations_grouped_by_area(indicator_code):
    area_repo = AreaRepository(recreate_db=False, config=sqlite_config)
    indicator_repo = IndicatorRepository(recreate_db=False, config=sqlite_config)
    observation_repo = ObservationRepository(recreate_db=False, area_repo=area_repo, indicator_repo=indicator_repo,
                                             config=sqlite_config)
    visualisation = observation_repo.find_observations_grouped_by_area_visualisation(indicator_code)
    return json_encoder(request, visualisation)


@app.route("/visualisationsGroupedByArea/<indicator_code>/<area_code>")
@cache.cached(timeout=TIMEOUT, key_prefix=make_cache_key)
def list_observations_by_indicator_and_country_visualisations_grouped_by_area(indicator_code, area_code):
    area_repo = AreaRepository(recreate_db=False, config=sqlite_config)
    indicator_repo = IndicatorRepository(recreate_db=False, config=sqlite_config)
    observation_repo = ObservationRepository(recreate_db=False, area_repo=area_repo, indicator_repo=indicator_repo,
                                             config=sqlite_config)
    visualisation = observation_repo.find_observations_grouped_by_area_visualisation(indicator_code, area_code)
    return json_encoder(request, visualisation)


@app.route("/visualisationsGroupedByArea/<indicator_code>/<area_code>/<year>")
@cache.cached(timeout=TIMEOUT, key_prefix=make_cache_key)
def list_observations_by_indicator_and_country_and_year_visualisations_grouped_by_area(indicator_code, area_code, year):
    area_repo = AreaRepository(recreate_db=False, config=sqlite_config)
    indicator_repo = IndicatorRepository(recreate_db=False, config=sqlite_config)
    observation_repo = ObservationRepository(recreate_db=False, area_repo=area_repo, indicator_repo=indicator_repo,
                                             config=sqlite_config)
    visualisation = observation_repo.find_observations_grouped_by_area_visualisation(indicator_code, area_code, year)
    return json_encoder(request, visualisation)


##########################################################################################
##                                        YEARS                                         ##
##########################################################################################

@app.route("/years")
@cache.cached(timeout=TIMEOUT, key_prefix=make_cache_key)
def list_observations_years():
    area_repo = AreaRepository(recreate_db=False, config=sqlite_config)
    indicator_repo = IndicatorRepository(recreate_db=False, config=sqlite_config)
    observation_repo = ObservationRepository(recreate_db=False, area_repo=area_repo, indicator_repo=indicator_repo,
                                             config=sqlite_config)
    years = observation_repo.get_year_list()
    return json_encoder(request, years)


@app.route("/years/array")
@cache.cached(timeout=TIMEOUT, key_prefix=make_cache_key)
def list_observations_years_array():
    area_repo = AreaRepository(recreate_db=False, config=sqlite_config)
    indicator_repo = IndicatorRepository(recreate_db=False, config=sqlite_config)
    observation_repo = ObservationRepository(recreate_db=False, area_repo=area_repo, indicator_repo=indicator_repo,
                                             config=sqlite_config)
    years = observation_repo.get_year_list()
    years_array = [year.value for year in years]
    return json_response_ok(request, years_array)


@app.errorhandler(RepositoryError)
def handle_repository_error(error):
    return json_response_error(request, error.message)


##########################################################################################
##                                        MAIN                                          ##
##########################################################################################

if __name__ == "__main__":
    app.debug = True
    app.run(host='0.0.0.0')

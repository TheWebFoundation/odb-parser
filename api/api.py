# #########################################################################################
##                                  INITIALISATIONS                                     ##
##########################################################################################
import os
import statistics
from collections import OrderedDict, deque
from configparser import RawConfigParser
from json import dumps
from operator import attrgetter

from flask import Flask, request, render_template, Response
from flask.ext.cache import Cache

from infrastructure.errors.errors import RepositoryError
from infrastructure.sql_repos.area_repository import AreaRepository
from infrastructure.sql_repos.indicator_repository import IndicatorRepository
from infrastructure.sql_repos.observation_repository import ObservationRepository

cache = Cache(config={'CACHE_TYPE': 'simple'})
app = Flask(__name__)
cache.init_app(app)

TIMEOUT = 30  # timeout to clean cache in seconds

sqlite_config = RawConfigParser()
sqlite_config.read(os.path.join(os.path.dirname(__file__), "api_sqlite_config.ini"))
sqlite_config.set("CONNECTION", "SQLITE_DB",
                  os.path.join(os.path.dirname(__file__), sqlite_config.get("CONNECTION", "SQLITE_DB")))


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


##########################################################################################
##                                     INDICATORS                                       ##
##########################################################################################

@app.route("/indicators")
@cache.cached(timeout=TIMEOUT, key_prefix=make_cache_key)
def list_indicators():
    indicators = IndicatorRepository(recreate_db=False, config=sqlite_config).find_indicators()
    return json_encoder(request, indicators)


@app.route("/indicators_flattened")
@cache.cached(timeout=TIMEOUT, key_prefix=make_cache_key)
def list_indicators_flattened():
    indicators = IndicatorRepository(recreate_db=False, config=sqlite_config).find_indicators()
    index_indicator = next(i for i in indicators if i.index is None)
    q = deque([index_indicator])
    final_indicators = []
    while q:
        i = q.popleft()
        print(i.indicator, len(q))
        final_indicators.append(i)
        q.extendleft(i.children)
        i.children = []

    # TODO: Uncomment to include orphan indicators (e.g. dataset_assesment)
    # final_indicators.extend([i for i in indicators if i not in final_indicators])
    return json_encoder(request, final_indicators)


@app.route("/indicators_meta")
@cache.cached(timeout=TIMEOUT, key_prefix=make_cache_key)
def list_indicators_meta():
    indicators = IndicatorRepository(recreate_db=False, config=sqlite_config).find_indicators()
    index_indicator = next(i for i in indicators if i.index is None)
    q = deque([index_indicator])
    final_indicators = []
    while q:
        i = q.popleft()
        print(i.indicator, len(q))
        final_indicators.append(i)
        q.extendleft(i.children)
        i.children = []

    # TODO: Uncomment to include orphan indicators (e.g. dataset_assesment)
    final_indicators = [i for i in indicators if i not in final_indicators]
    return json_encoder(request, final_indicators)


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


## Ad-hoc queries

@app.route("/yearsWithIndicatorData")
@cache.cached(timeout=TIMEOUT, key_prefix=make_cache_key)
def years_with_indicator_data():
    area_repo = AreaRepository(recreate_db=False, config=sqlite_config)
    indicator_repo = IndicatorRepository(recreate_db=False, config=sqlite_config)
    observation_repo = ObservationRepository(recreate_db=False, area_repo=area_repo, indicator_repo=indicator_repo,
                                             config=sqlite_config)

    query_result = observation_repo._get_years_with_indicator()
    data = {}
    for (year, indicator) in query_result:
        if year not in data:
            data[year] = []
        data[year].append(indicator)

    return json_response_ok(request, data)


@app.route("/indexObservations/<year>")
@cache.cached(timeout=TIMEOUT, key_prefix=make_cache_key)
def indexObservations_by_year(year):
    area_repo = AreaRepository(recreate_db=False, config=sqlite_config)
    indicator_repo = IndicatorRepository(recreate_db=False, config=sqlite_config)
    observation_repo = ObservationRepository(recreate_db=False, area_repo=area_repo, indicator_repo=indicator_repo,
                                             config=sqlite_config)
    index_indicator = indicator_repo.find_indicators_index()[0]
    observations = observation_repo.find_tree_observations(index_indicator.indicator, 'ALL', year, 'INDICATOR')
    areas = area_repo.find_countries(order="iso3")

    data = {'year': year, 'areas': OrderedDict(), 'stats': OrderedDict()}
    for area in sorted(areas, key=attrgetter('iso3')):
        for obs in sorted([obs for obs in observations if obs.area.iso3 == area.iso3],
                          key=lambda o: o.indicator.indicator):
            if area.iso3 not in data['areas']:
                data['areas'][area.iso3] = OrderedDict()
            data['areas'][area.iso3][obs.indicator.indicator] = {
                'value': obs.value,
                'rank': obs.rank,
                'rank_change': obs.rank_change
            }

    for indicator_code in sorted(set([o.indicator.indicator for o in observations])):
        per_indicator_obs = [o.value for o in observations if
                             o.indicator.indicator == indicator_code and o.value is not None]
        if indicator_code not in data['stats']:
            data['stats'][indicator_code] = OrderedDict()
        data['stats'][indicator_code][':::'] = OrderedDict()
        data['stats'][indicator_code][':::']['mean'] = statistics.mean(per_indicator_obs)
        data['stats'][indicator_code][':::']['median'] = statistics.median(per_indicator_obs)
        for region in area_repo.find_regions():
            per_region_obs = [o.value for o in observations if
                              o.indicator.indicator == indicator_code and o.value is not None and o.area.iso3 in [c.iso3
                                                                                                                  for c
                                                                                                                  in
                                                                                                                  region.countries]]
            data['stats'][indicator_code][region.iso3] = OrderedDict()
            data['stats'][indicator_code][region.iso3]['mean'] = statistics.mean(per_region_obs)
            data['stats'][indicator_code][region.iso3]['median'] = statistics.median(per_region_obs)

    return json_response_ok(request, data)


@app.route("/indexEvolution/<year>")
@cache.cached(timeout=TIMEOUT, key_prefix=make_cache_key)
def indexEvolution_by_year(year):
    area_repo = AreaRepository(recreate_db=False, config=sqlite_config)
    indicator_repo = IndicatorRepository(recreate_db=False, config=sqlite_config)
    observation_repo = ObservationRepository(recreate_db=False, area_repo=area_repo, indicator_repo=indicator_repo,
                                             config=sqlite_config)
    index_indicator = indicator_repo.find_indicators_index()[0]
    observations = observation_repo.find_tree_observations(index_indicator.indicator, 'ALL', None, 'COMPONENT')
    areas = area_repo.find_countries(order="iso3")

    data = {'year': year, 'areas': OrderedDict(), 'stats': OrderedDict()}
    for area in sorted(areas, key=attrgetter('iso3')):
        for obs in sorted([obs for obs in observations if obs.area.iso3 == area.iso3],
                          key=lambda o: o.indicator.indicator):
            if area.iso3 not in data['areas']:
                data['areas'][area.iso3] = OrderedDict()
            if obs.indicator.indicator not in data['areas'][area.iso3]:
                data['areas'][area.iso3][obs.indicator.indicator] = OrderedDict()

            if obs.year == int(year):
                data['areas'][area.iso3][obs.indicator.indicator]['value'] = obs.value
                if obs.indicator.type == 'INDEX':
                    data['areas'][area.iso3][obs.indicator.indicator]['rank'] = obs.rank
                    data['areas'][area.iso3][obs.indicator.indicator]['rank_change'] = obs.rank_change

            if obs.indicator.type == 'INDEX':
                if 'rank_evolution' not in data['areas'][area.iso3][obs.indicator.indicator]:
                    data['areas'][area.iso3][obs.indicator.indicator]['rank_evolution'] = []
                    # data['areas'][area.iso3][obs.indicator.indicator]['value_evolution'] = []
                data['areas'][area.iso3][obs.indicator.indicator]['rank_evolution'].append(
                    {'year': obs.year, 'value': obs.rank})
                # data['areas'][area.iso3][obs.indicator.indicator]['value_evolution'].append(
                #     {'year': obs.year, 'value': obs.value})

    # Clean areas without data that year
    for area in list(data['areas'].keys()):
        if 'value' not in data['areas'][area]['ODB']:
            del data['areas'][area]

    for indicator_code in sorted(set([o.indicator.indicator for o in observations])):
        per_indicator_obs = [o.value for o in observations if
                             o.indicator.indicator == indicator_code and o.value is not None]
        if indicator_code not in data['stats']:
            data['stats'][indicator_code] = OrderedDict()
        data['stats'][indicator_code][':::'] = OrderedDict()
        data['stats'][indicator_code][':::']['mean'] = statistics.mean(per_indicator_obs)
        data['stats'][indicator_code][':::']['median'] = statistics.median(per_indicator_obs)
        for region in area_repo.find_regions():
            per_region_obs = [o.value for o in observations if
                              o.indicator.indicator == indicator_code and o.value is not None and o.area.iso3 in [c.iso3
                                                                                                                  for c
                                                                                                                  in
                                                                                                                  region.countries]]
            data['stats'][indicator_code][region.iso3] = OrderedDict()
            data['stats'][indicator_code][region.iso3]['mean'] = statistics.mean(per_region_obs)
            data['stats'][indicator_code][region.iso3]['median'] = statistics.median(per_region_obs)

    return json_response_ok(request, data)


# @app.route("/indexStats/<year>")
# @cache.cached(timeout=TIMEOUT, key_prefix=make_cache_key)
# def indexStats_by_year(year):
#     area_repo = AreaRepository(recreate_db=False, config=sqlite_config)
#     indicator_repo = IndicatorRepository(recreate_db=False, config=sqlite_config)
#     observation_repo = ObservationRepository(recreate_db=False, area_repo=area_repo, indicator_repo=indicator_repo,
#                                              config=sqlite_config)
#     index_indicator = indicator_repo.find_indicators_index()[0]
#     observations = observation_repo.find_tree_observations(index_indicator.indicator, 'ALL', year, 'INDICATOR')
#     areas = area_repo.find_countries(order="iso3")
#
#     data = {'year': year, 'stats': OrderedDict()}
#
#     for indicator_code in sorted(set([o.indicator.indicator for o in observations])):
#         per_indicator_obs = [o.value for o in observations if
#                              o.indicator.indicator == indicator_code and o.value is not None]
#         if indicator_code not in data['stats']:
#             data['stats'][indicator_code] = OrderedDict()
#         data['stats'][indicator_code][':::'] = OrderedDict()
#         data['stats'][indicator_code][':::']['mean'] = statistics.mean(per_indicator_obs)
#         data['stats'][indicator_code][':::']['median'] = statistics.median(per_indicator_obs)
#         for region in area_repo.find_regions():
#             per_region_obs = [o.value for o in observations if
#                               o.indicator.indicator == indicator_code
#                               and o.value is not None
#                               and o.area.iso3 in [c.iso3 for c in region.countries]]
#             data['stats'][indicator_code][region.iso3] = OrderedDict()
#             data['stats'][indicator_code][region.iso3]['mean'] = statistics.mean(per_region_obs)
#             data['stats'][indicator_code][region.iso3]['median'] = statistics.median(per_region_obs)
#
#     return json_response_ok(request, data)

@app.route("/indexStats/<year>")
@cache.cached(timeout=TIMEOUT, key_prefix=make_cache_key)
def indexStats_by_year(year):
    area_repo = AreaRepository(recreate_db=False, config=sqlite_config)
    indicator_repo = IndicatorRepository(recreate_db=False, config=sqlite_config)
    observation_repo = ObservationRepository(recreate_db=False, area_repo=area_repo, indicator_repo=indicator_repo,
                                             config=sqlite_config)
    index_indicator = indicator_repo.find_indicators_index()[0]
    observations = observation_repo.find_tree_observations(index_indicator.indicator, 'ALL', year, 'INDICATOR')
    areas = area_repo.find_countries(order="iso3")

    data = {'year': year, 'stats': OrderedDict()}

    for region in area_repo.find_regions():
        per_region_obs = [o for o in observations if o.value is not None
                          and o.area.iso3 in [c.iso3 for c in region.countries]]
        for indicator_code in sorted(set([o.indicator.indicator for o in observations])):
            per_indicator_obs = [o.value for o in per_region_obs if
                                 o.indicator.indicator == indicator_code and o.value is not None]
            if region.iso3 not in data['stats']:
                data['stats'][region.iso3] = OrderedDict()
            data['stats'][region.iso3][indicator_code] = OrderedDict()
            data['stats'][region.iso3][indicator_code]['mean'] = statistics.mean(per_indicator_obs)
            data['stats'][region.iso3][indicator_code]['median'] = statistics.median(per_indicator_obs)

    data['stats'][':::'] = OrderedDict()
    for indicator_code in sorted(set([o.indicator.indicator for o in observations])):
        per_indicator_obs = [o.value for o in observations if
                             o.indicator.indicator == indicator_code and o.value is not None]
        data['stats'][':::'][indicator_code] = OrderedDict()
        data['stats'][':::'][indicator_code]['mean'] = statistics.mean(per_indicator_obs)
        data['stats'][':::'][indicator_code]['median'] = statistics.median(per_indicator_obs)

    return json_response_ok(request, data)


@app.route("/countryObservations/<area_code>")
@cache.cached(timeout=TIMEOUT, key_prefix=make_cache_key)
def countryObservations_by_area(area_code):
    area_repo = AreaRepository(recreate_db=False, config=sqlite_config)
    indicator_repo = IndicatorRepository(recreate_db=False, config=sqlite_config)
    observation_repo = ObservationRepository(recreate_db=False, area_repo=area_repo, indicator_repo=indicator_repo,
                                             config=sqlite_config)

    index_indicator = indicator_repo.find_indicators_index()[0]

    data = {'area': area_code, 'years': OrderedDict()}

    for year in sorted([str(y.value) for y in observation_repo.get_year_list()]):
        observations = observation_repo.find_tree_observations(index_indicator.indicator, area_code, year, 'INDICATOR',
                                                               False)
        if not observations: continue;
        data['years'][year] = {'observations': OrderedDict(), 'stats': OrderedDict(), 'datasets': OrderedDict()}
        for obs in sorted([obs for obs in observations if obs.dataset_indicator is None],
                          key=lambda o: o.indicator.indicator):
            data['years'][year]['observations'][obs.indicator.indicator] = {
                'value': obs.value,
                'rank': obs.rank,
                'rank_change': obs.rank_change
            }

        indicators_with_dataset = sorted(
            set([obs.indicator.indicator for obs in observations if obs.dataset_indicator is not None]))
        for indicator in indicators_with_dataset:
            dataset_observations = sorted([obs for obs in observations if obs.indicator.indicator == indicator],
                                          key=lambda o: o.indicator.indicator)
            data['years'][year]['datasets'][indicator] = OrderedDict()
            for obs in dataset_observations:
                if obs.dataset_indicator is None:
                    data['years'][year]['datasets'][obs.indicator.indicator]['VALUE'] = obs.value
                else:
                    data['years'][year]['datasets'][obs.indicator.indicator][
                        obs.dataset_indicator.indicator] = obs.value

        for indicator_code in sorted(set([o.indicator.indicator for o in observations])):
            per_indicator_obs = [o.value for o in observations if
                                 o.indicator.indicator == indicator_code and o.value is not None and o.dataset_indicator is None]
            data['years'][year]['stats'][indicator_code] = OrderedDict()
            data['years'][year]['stats'][indicator_code]['mean'] = statistics.mean(
                per_indicator_obs) if per_indicator_obs else None
            data['years'][year]['stats'][indicator_code]['median'] = statistics.median(
                per_indicator_obs) if per_indicator_obs else None

            # assert (data['years'][year]['observations'])
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

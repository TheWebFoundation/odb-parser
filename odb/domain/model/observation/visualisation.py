from odb.domain.model.observation.statistics import Statistics


class Visualisation(object):
    """
    Visualisations entity

    Attributes:
        observations (list of Observations): Observations for the visualization
        statistics (Statistics): Statistics for the visualization
    """

    def __init__(self, observations, observations_all_areas=None):
        """
        Constructor for Visualization

        Args:
            observations (list of Observation): Observations to store and calculate statistics
            observations_all_areas (list of Observations, optional): All observations without area filters
        """

        self._observations = observations
        self._statistics = Statistics(observations)
        self._observations_all_areas = observations_all_areas if observations_all_areas else []
        self._statistics_all_areas = Statistics(observations_all_areas)

    @property
    def observations(self):
        return self._observations

    @property
    def statistics(self):
        return self._statistics

    @property
    def statistics_all_areas(self):
        return self._statistics_all_areas

    def to_dict(self):
        """
        Converts self object to dictionary

        Returns:
            dict: Dictionary representation of self object
        """
        d = self.to_dict_without_all_areas()
        d['statistics_all_areas'] = self.statistics_all_areas.to_dict()
        return d

    def to_dict_without_all_areas(self):
        """
        Converts self object to dictionary without statistics for all countries

        Returns:
            dict: Dictionary representation of self object
        """
        return {
            'observations': [obs.to_dict() for obs in self.observations],
            'statistics': self.statistics.to_dict(),
        }

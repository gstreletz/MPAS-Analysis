# -*- coding: utf-8 -*-
#
# Copyright (c) 2017,  Los Alamos National Security, LLC (LANS)
# and the University Corporation for Atmospheric Research (UCAR).
#
# Unless noted otherwise source code is licensed under the BSD license.
# Additional copyright and license information can be found in the LICENSE file
# distributed with this code, or at http://mpas-dev.github.com/license.html
#

from __future__ import absolute_import, division, print_function, \
    unicode_literals

from mpas_analysis.shared import AnalysisTask

from mpas_analysis.ocean.compute_anomaly_subtask import ComputeAnomalySubtask
from mpas_analysis.ocean.plot_hovmoller_subtask import PlotHovmollerSubtask


class TimeSeriesTemperatureAnomaly(AnalysisTask):
    """
    Performs analysis of time series of temperature anomalies from the first
    simulation year as a function of depth.
    """
    # Authors
    # -------
    # Xylar Asay-Davis

    def __init__(self, config, mpasTimeSeriesTask):  # {{{
        """
        Construct the analysis task.

        Parameters
        ----------
        config :  instance of MpasAnalysisConfigParser
            Contains configuration options

        mpasTimeSeriesTask : ``MpasTimeSeriesTask``
            The task that extracts the time series from MPAS monthly output
        """
        # Authors
        # -------
        # Xylar Asay-Davis

        # first, call the constructor from the base class (AnalysisTask)
        super(TimeSeriesTemperatureAnomaly, self).__init__(
            config=config,
            taskName='timeSeriesTemperatureAnomaly',
            componentName='ocean',
            tags=['timeSeries', 'temperature'])

        sectionName = 'hovmollerTemperatureAnomaly'
        regionNames = config.getExpression(sectionName, 'regions')
        movingAveragePoints = config.getint(sectionName, 'movingAveragePoints')

        mpasFieldName = 'timeMonthly_avg_avgValueWithinOceanLayerRegion_' \
            'avgLayerTemperature'

        timeSeriesFileName = 'regionAveragedTemperatureAnomaly.nc'

        anomalyTask = ComputeAnomalySubtask(
                parentTask=self,
                mpasTimeSeriesTask=mpasTimeSeriesTask,
                outFileName=timeSeriesFileName,
                variableList=[mpasFieldName],
                movingAveragePoints=movingAveragePoints)
        self.add_subtask(anomalyTask)

        for regionName in regionNames:
            caption = 'Trend of {} Temperature Anomaly vs depth'.format(
                    regionName)
            plotTask = PlotHovmollerSubtask(
                    parentTask=self,
                    regionName=regionName,
                    inFileName=timeSeriesFileName,
                    outFileLabel='TAnomalyZ',
                    fieldNameInTitle='Temperature Anomaly',
                    mpasFieldName=mpasFieldName,
                    unitsLabel='[$^\circ$C]',
                    sectionName=sectionName,
                    thumbnailSuffix=u'ΔT',
                    imageCaption=caption,
                    galleryGroup='Trends vs Depth',
                    groupSubtitle=None,
                    groupLink='trendsvsdepth',
                    galleryName=None)

            plotTask.run_after(anomalyTask)
            self.add_subtask(plotTask)

        # }}}

    # }}}

# vim: foldmethod=marker ai ts=4 sts=4 et sw=4 ft=python

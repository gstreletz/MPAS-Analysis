# Copyright (c) 2017,  Los Alamos National Security, LLC (LANS)
# and the University Corporation for Atmospheric Research (UCAR).
#
# Unless noted otherwise source code is licensed under the BSD license.
# Additional copyright and license information can be found in the LICENSE file
# distributed with this code, or at http://mpas-dev.github.com/license.html
#

from __future__ import absolute_import, division, print_function, \
    unicode_literals

import os
import subprocess
from distutils.spawn import find_executable
import xarray as xr
import numpy

from mpas_analysis.shared.analysis_task import AnalysisTask

from mpas_analysis.shared.io.utility import build_config_full_path, \
    make_directories, get_files_year_month
from mpas_analysis.shared.timekeeping.utility import get_simulation_start_time


class MpasTimeSeriesTask(AnalysisTask):  # {{{
    '''
    An analysis tasks for computing time series from output from the
    ``timeSeriesStatsMonthly`` analysis member.

    Attributes
    ----------

    variableList : list of str
        A list of variable names in ``timeSeriesStatsMonthly`` to be
        included in the time series

    allVariables : list of str
        A list of all available variable names in ``timeSeriesStatsMonthly``
        used to raise an exception when an unavailable variable is requested

    inputFiles : list of str
        A list of input files from which to extract the time series.

    startDate, endDate : str
        The start and end dates of the time series as strings

    startYear, endYear : int
        The start and end years of the time series
    '''
    # Authors
    # -------
    # Xylar Asay-Davis

    def __init__(self, config, componentName, taskName=None,
                 subtaskName=None, section='timeSeries'):  # {{{
        '''
        Construct the analysis task for extracting time series.

        Parameters
        ----------
        config : ``MpasAnalysisConfigParser``
            Contains configuration options

        componentName : {'ocean', 'seaIce'}
            The name of the component (same as the folder where the task
            resides)

        taskName : str, optional
            The name of the task, 'mpasTimeSeriesOcean' or
            'mpasTimeSeriesSeaIce' by default (depending on ``componentName``)

        subtaskName : str, optional
            The name of the subtask (if any)

        section : str, optional
            The section of the config file from which to read the start and
            end times for the time series, also added as a tag
        '''
        # Authors
        # -------
        # Xylar Asay-Davis

        self.variableList = []
        self.section = section
        tags = [section]

        self.allVariables = None

        if taskName is None:
            suffix = section[0].upper() + section[1:] + \
                componentName[0].upper() + componentName[1:]
            taskName = 'mpas{}'.format(suffix)

        # call the constructor from the base class (AnalysisTask)
        super(MpasTimeSeriesTask, self).__init__(
            config=config,
            taskName=taskName,
            subtaskName=subtaskName,
            componentName=componentName,
            tags=tags)

        # }}}

    def add_variables(self, variableList):  # {{{
        '''
        Add one or more variables to extract as a time series.

        Parameters
        ----------
        variableList : list of str
            A list of variable names in ``timeSeriesStatsMonthly`` to be
            included in the time series

        Raises
        ------
        ValueError
            if this funciton is called before this task has been set up (so
            the list of available variables has not yet been set) or if one
            or more of the requested variables is not available in the
            ``timeSeriesStatsMonthly`` output.
        '''
        # Authors
        # -------
        # Xylar Asay-Davis

        if self.allVariables is None:
            raise ValueError('add_variables() can only be called after '
                             'setup_and_check() in MpasTimeSeriesTask.\n'
                             'Presumably tasks were added in the wrong order '
                             'or add_variables() is being called in the wrong '
                             'place.')

        for variable in variableList:
            if variable not in self.allVariables:
                raise ValueError(
                        '{} is not available in timeSeriesStatsMonthly '
                        'output:\n{}'.format(variable, self.allVariables))

            if variable not in self.variableList:
                self.variableList.append(variable)

        # }}}

    def setup_and_check(self):  # {{{
        '''
        Perform steps to set up the analysis and check for errors in the setup.
        '''
        # Authors
        # -------
        # Xylar Asay-Davis

        # first, call setup_and_check from the base class (AnalysisTask),
        # which will perform some common setup, including storing:
        #     self.runDirectory , self.historyDirectory, self.plotsDirectory,
        #     self.namelist, self.runStreams, self.historyStreams,
        #     self.calendar
        super(MpasTimeSeriesTask, self).setup_and_check()

        config = self.config
        baseDirectory = build_config_full_path(
            config, 'output', 'timeSeriesSubdirectory')

        make_directories(baseDirectory)

        self.outputFile = '{}/{}.nc'.format(baseDirectory,
                                            self.fullTaskName)

        self.check_analysis_enabled(
            analysisOptionName='config_am_timeseriesstatsmonthly_enable',
            raiseException=True)

        # get a list of timeSeriesStats output files from the streams file,
        # reading only those that are between the start and end dates
        startDate = config.get(self.section, 'startDate')
        endDate = config.get(self.section, 'endDate')
        streamName = 'timeSeriesStatsMonthlyOutput'
        self.inputFiles = self.historyStreams.readpath(
                streamName, startDate=startDate, endDate=endDate,
                calendar=self.calendar)

        if len(self.inputFiles) == 0:
            raise IOError('No files were found in stream {} between {} and '
                          '{}.'.format(streamName, startDate, endDate))

        self._update_time_series_bounds_from_file_names()

        self.runMessage = '\nComputing MPAS time series from first year ' \
                          'plus files:\n' \
                          '    {} through\n    {}'.format(
                                  os.path.basename(self.inputFiles[0]),
                                  os.path.basename(self.inputFiles[-1]))

        # Make sure first year of data is included for computing anomalies
        if config.has_option('timeSeries', 'anomalyRefYear'):
            anomalyYear = config.getint('timeSeries', 'anomalyRefYear')
            anomalyStartDate = '{:04d}-01-01_00:00:00'.format(anomalyYear)
        else:
            anomalyStartDate = get_simulation_start_time(self.runStreams)
            anomalyYear = int(anomalyStartDate[0:4])

        anomalyEndDate = '{:04d}-12-31_23:59:59'.format(anomalyYear)
        firstYearInputFiles = self.historyStreams.readpath(
                streamName, startDate=anomalyStartDate,
                endDate=anomalyEndDate,
                calendar=self.calendar)
        for fileName in firstYearInputFiles:
            if fileName not in self.inputFiles:
                self.inputFiles.append(fileName)

        self.inputFiles = sorted(self.inputFiles)

        with xr.open_dataset(self.inputFiles[0]) as ds:
            self.allVariables = list(ds.data_vars.keys())

        # }}}

    def run_task(self):  # {{{
        '''
        Compute the requested time series
        '''
        # Authors
        # -------
        # Xylar Asay-Davis

        if len(self.variableList) == 0:
            # nothing to do
            return

        self.logger.info(self.runMessage)

        self._compute_time_series_with_ncrcat()

        # }}}

    def _update_time_series_bounds_from_file_names(self):  # {{{
        """
        Update the start and end years and dates for time series based on the
        years actually available in the list of files.
        """
        # Authors
        # -------
        # Xylar Asay-Davis

        config = self.config
        section = self.section

        requestedStartYear = config.getint(section, 'startYear')
        requestedEndYear = config.getint(section, 'endYear')

        fileNames = sorted(self.inputFiles)
        years, months = get_files_year_month(fileNames,
                                             self.historyStreams,
                                             'timeSeriesStatsMonthlyOutput')

        # search for the start of the first full year
        firstIndex = 0
        while(firstIndex < len(years) and months[firstIndex] != 1):
            firstIndex += 1
        startYear = years[firstIndex]

        # search for the end of the last full year
        lastIndex = len(years)-1
        while(lastIndex >= 0 and months[lastIndex] != 12):
            lastIndex -= 1
        endYear = years[lastIndex]

        if startYear != requestedStartYear or endYear != requestedEndYear:
            print("Warning: {} start and/or end year different from "
                  "requested\n"
                  "requestd: {:04d}-{:04d}\n"
                  "actual:   {:04d}-{:04d}\n".format(section,
                                                     requestedStartYear,
                                                     requestedEndYear,
                                                     startYear,
                                                     endYear))
            config.set(section, 'startYear', str(startYear))
            config.set(section, 'endYear', str(endYear))

            startDate = '{:04d}-01-01_00:00:00'.format(startYear)
            config.set(section, 'startDate', startDate)
            endDate = '{:04d}-12-31_23:59:59'.format(endYear)
            config.set(section, 'endDate', endDate)
        else:
            startDate = config.get(section, 'startDate')
            endDate = config.get(section, 'endDate')

        self.startDate = startDate
        self.endDate = endDate
        self.startYear = startYear
        self.endYear = endYear

        # }}}

    def _compute_time_series_with_ncrcat(self):
        # {{{
        '''
        Uses ncrcat to extact time series from timeSeriesMonthlyOutput files

        Raises
        ------
        OSError
            If ``ncrcat`` is not in the system path.

        Author
        ------
        Xylar Asay-Davis
        '''

        if find_executable('ncrcat') is None:
            raise OSError('ncrcat not found. Make sure the latest nco '
                          'package is installed: \n'
                          'conda install nco\n'
                          'Note: this presumes use of the conda-forge '
                          'channel.')

        inputFiles = self.inputFiles
        if os.path.exists(self.outputFile):
            # make sure all the necessary variables are also present
            with xr.open_dataset(self.outputFile) as ds:
                updateSubset = True
                for variableName in self.variableList:
                    if variableName not in ds.variables:
                        updateSubset = False
                        break

                if updateSubset:
                    # add only input files wiht times that aren't already in
                    # the output file

                    fileNames = sorted(self.inputFiles)
                    inYears, inMonths = get_files_year_month(
                            fileNames, self.historyStreams,
                            'timeSeriesStatsMonthlyOutput')

                    inYears = numpy.array(inYears)
                    inMonths = numpy.array(inMonths)
                    totalMonths = 12*inYears + inMonths

                    dates = [bytes.decode(name) for name in
                             ds.xtime_startMonthly.values]
                    lastDate = dates[-1]

                    lastYear = int(lastDate[0:4])
                    lastMonth = int(lastDate[5:7])
                    lastTotalMonths = 12*lastYear + lastMonth

                    inputFiles = []
                    for index, inputFile in enumerate(fileNames):
                        if totalMonths[index] > lastTotalMonths:
                            inputFiles.append(inputFile)

                    if len(inputFiles) == 0:
                        # nothing to do
                        return
                else:
                    # there is an output file but it has the wrong variables
                    # so we need ot delete it.
                    self.logger.warning('Warning: deleting file {} because '
                                        'some variables were missing'.format(
                                                self.outputFile))
                    os.remove(self.outputFile)

        variableList = self.variableList + ['xtime_startMonthly',
                                            'xtime_endMonthly']

        args = ['ncrcat', '-4', '--record_append', '--no_tmp_fl',
                '-v', ','.join(variableList)]

        printCommand = '{} {} ... {} {}'.format(' '.join(args), inputFiles[0],
                                                inputFiles[-1],
                                                self.outputFile)
        args.extend(inputFiles)
        args.append(self.outputFile)

        self.logger.info('running: {}'.format(printCommand))
        for handler in self.logger.handlers:
            handler.flush()

        process = subprocess.Popen(args, stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE)
        stdout, stderr = process.communicate()

        if stdout:
            stdout = stdout.decode('utf-8')
            for line in stdout.split('\n'):
                self.logger.info(line)
        if stderr:
            stderr = stderr.decode('utf-8')
            for line in stderr.split('\n'):
                self.logger.error(line)

        if process.returncode != 0:
            raise subprocess.CalledProcessError(process.returncode,
                                                ' '.join(args))

        # }}}
    # }}}


# vim: foldmethod=marker ai ts=4 sts=4 et sw=4 ft=python

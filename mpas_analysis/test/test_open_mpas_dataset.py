# Copyright (c) 2017,  Los Alamos National Security, LLC (LANS)
# and the University Corporation for Atmospheric Research (UCAR).
#
# Unless noted otherwise source code is licensed under the BSD license.
# Additional copyright and license information can be found in the LICENSE file
# distributed with this code, or at http://mpas-dev.github.com/license.html
#
"""
Unit test infrastructure for the generalized_reader.

Xylar Asay-Davis
02/16/2017
"""

from __future__ import absolute_import, division, print_function, \
    unicode_literals

import pytest
from mpas_analysis.test import TestCase, loaddatadir
from mpas_analysis.shared.io import open_mpas_dataset


@pytest.mark.usefixtures("loaddatadir")
class TestOpenMpasDataset(TestCase):

    def test_open_dataset_fn(self):
        fileName = str(self.datadir.join('example_jan.nc'))
        timestr = ['xtime_start', 'xtime_end']
        variableList = \
            ['time_avg_avgValueWithinOceanRegion_avgSurfaceTemperature']

        for calendar in ['gregorian', 'gregorian_noleap']:
            ds = open_mpas_dataset(
                fileName=fileName,
                calendar=calendar,
                timeVariableNames=timestr,
                variableList=variableList)
            self.assertEqual(list(ds.data_vars.keys()), variableList)

    def test_start_end(self):
        fileName = str(self.datadir.join('example_jan_feb.nc'))
        timestr = ['xtime_start', 'xtime_end']
        variableList = \
            ['time_avg_avgValueWithinOceanRegion_avgSurfaceTemperature']

        for calendar in ['gregorian', 'gregorian_noleap']:
            # all dates
            ds = open_mpas_dataset(
                fileName=fileName,
                calendar=calendar,
                timeVariableNames=timestr,
                variableList=variableList,
                startDate='0001-01-01',
                endDate='9999-12-31')
            self.assertEqual(len(ds.Time), 2)

            # just the first date
            ds = open_mpas_dataset(
                fileName=fileName,
                calendar=calendar,
                timeVariableNames=timestr,
                variableList=variableList,
                startDate='0005-01-01',
                endDate='0005-02-01')
            self.assertEqual(len(ds.Time), 1)

            # just the second date
            ds = open_mpas_dataset(
                fileName=fileName,
                calendar=calendar,
                timeVariableNames=timestr,
                variableList=variableList,
                startDate='0005-02-01',
                endDate='0005-03-01')
            self.assertEqual(len(ds.Time), 1)

    def test_open_process_climatology(self):
        fileName = str(self.datadir.join('timeSeries.nc'))
        calendar = 'gregorian_noleap'
        open_mpas_dataset(
            fileName=fileName,
            calendar=calendar,
            timeVariableNames=['xtime_startMonthly', 'xtime_endMonthly'],
            variableList=['timeMonthly_avg_tThreshMLD'])

# vim: foldmethod=marker ai ts=4 sts=4 et sw=4 ft=python

# This software is open source software available under the BSD-3 license.
#
# Copyright (c) 2018 Los Alamos National Security, LLC. All rights reserved.
# Copyright (c) 2018 Lawrence Livermore National Security, LLC. All rights
# reserved.
# Copyright (c) 2018 UT-Battelle, LLC. All rights reserved.
#
# Additional copyright and license information can be found in the LICENSE file
# distributed with this code, or at
# https://raw.githubusercontent.com/MPAS-Dev/MPAS-Analysis/master/LICENSE
from __future__ import absolute_import, division, print_function, \
    unicode_literals

import xarray as xr

from mpas_analysis.ocean.compute_transects_subtask import \
    ComputeTransectsSubtask


class ComputeTransectsWithVelMag(ComputeTransectsSubtask):  # {{{
    """
    Add velocity magnitude from zonal and meridional components to observations
    """
    # Authors
    # -------
    # Xylar Asay-Davis

    def customize_masked_climatology(self, climatology, season):  # {{{
        """
        Construct velocity magnitude as part of the climatology

        Parameters
        ----------
        climatology : ``xarray.Dataset`` object
            the climatology data set

        season : str
            The name of the season to be masked

        Returns
        -------
        climatology : ``xarray.Dataset`` object
            the modified climatology data set
        """
        # Authors
        # -------
        # Xylar Asay-Davis

        # first, call the base class's version of this function so we extract
        # the desired slices.
        climatology = super(ComputeTransectsWithVelMag,
                            self).customize_masked_climatology(climatology,
                                                               season)

        if 'timeMonthly_avg_velocityZonal' in climatology and \
                'timeMonthly_avg_velocityMeridional' in climatology:
            zonalVel = climatology.timeMonthly_avg_velocityZonal
            meridVel = climatology.timeMonthly_avg_velocityMeridional
            climatology['velMag'] = xr.ufuncs.sqrt(zonalVel**2 + meridVel**2)
            climatology.velMag.attrs['units'] = 'm s$^{-1}$'
            climatology.velMag.attrs['description'] = 'velocity magnitude'

        return climatology  # }}}

    # }}}


# vim: foldmethod=marker ai ts=4 sts=4 et sw=4 ft=python

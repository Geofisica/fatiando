# Copyright 2010 The Fatiando a Terra Development Team
#
# This file is part of Fatiando a Terra.
#
# Fatiando a Terra is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Fatiando a Terra is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with Fatiando a Terra.  If not, see <http://www.gnu.org/licenses/>.
"""
Create synthetic gravity data from various types of model.

Functions:

* :func:`fatiando.grav.synthetic.from_prisms`
    Create synthetic data from a prism model.

* :func:`fatiando.grav.synthetic.from_spheres`
    Create synthetic gravity data from a model made of spheres.
    
"""
__author__ = 'Leonardo Uieda (leouieda@gmail.com)'
__date__ = 'Created 11-Sep-2010'


import logging
import time

import numpy

import fatiando
import fatiando.grav.prism
import fatiando.grav.sphere


# Add the default handler (a null handler) to the logger to ensure that
# it won't print verbose if the program calling them doesn't want it
log = logging.getLogger('fatiando.grav.synthetic')
log.addHandler(fatiando.default_log_handler)


def from_prisms(prisms, x1, x2, y1, y2, nx, ny, height, field='gz', 
                grid='regular'):
    """
    Create synthetic gravity data from a prism model.
    
    Note: to make a profile along x, set ``y1=y2`` and ``ny=1``
    
    Parameters:
      
    * prisms
        List of prisms in the model. (see :func:`fatiando.geometry.prism`)
            
    * x1, x2
        Limits in the x direction of the region where the data will be computed
            
    * y1, y2
        Limits in the y direction of the region where the data will be computed
            
    * nx, ny
        Number of data points in the x and y directions
    
    * height
        Height at which the data will be computed (scalar for constant height or
        1D array with height at each x,y pair)
    
    * field
        What component of the gravity field to calculate. Can be any one of
        ``'gz'``, ``'gxx'``, ``'gxy'``, ``'gxz'``, ``'gyy'``, ``'gyz'``, 
        ``'gzz'``
          
    * grid
        Distribution of the data along the selected region. Can be either
        ``'regular'`` or ``'random'``
            
    Returns:
        
    * data        
        Gravity field data stored in a dictionary.
        
    The data dictionary will be such as::
    
        {'x':[x1, x2, ...], 'y':[y1, y2, ...], 'z':[z1, z2, ...],
         'value':[data1, data2, ...], 'error':[error1, error2, ...],
         'grid':True or False, 'nx':points_in_x, 'ny':points_in_y}
    
    ``'grid'`` will be true if calculating on a ``'regular'`` grid.
    The keys ``nx`` and ``ny`` are only required if ``grid`` is ``True``.
    """
    
    assert grid in ['regular', 'random'], "Invalid grid type '%s'" % (grid)
    
    fields = {'gz':fatiando.grav.prism.gz, 
              'gxx':fatiando.grav.prism.gxx, 
              'gxy':fatiando.grav.prism.gxy, 
              'gxz':fatiando.grav.prism.gxz, 
              'gyy':fatiando.grav.prism.gyy, 
              'gyz':fatiando.grav.prism.gyz, 
              'gzz':fatiando.grav.prism.gzz}    
    
    assert field in fields.keys(), "Invalid gravity field '%s'" % (field)
    
    data = {'z':-height*numpy.ones(nx*ny), 'value':numpy.zeros(nx*ny), 
            'error':numpy.zeros(nx*ny)}
               
    log.info("Generating synthetic %s data:" % (field))
    
    if grid == 'regular':
        
        log.info("  grid type: regular")
        
        dx = float(x2 - x1)/(nx - 1)
        x_range = numpy.arange(x1, x2, dx)
        
        if ny > 1:
            
            dy = float(y2 - y1)/(ny - 1)
            y_range = numpy.arange(y1, y2, dy)
            
        else:
            
            dy = 0
            y_range = [y1]
        
        if len(x_range) < nx:
            
            x_range = numpy.append(x_range, x2)
        
        if len(y_range) < ny:
            
            y_range = numpy.append(y_range, y2)
            
        xs = []
        ys = []
        
        for y in y_range:
            
            for x in x_range:
                
                xs.append(x)
                ys.append(y)
                
        xs = numpy.array(xs)
        ys = numpy.array(ys)
        
        data['grid'] = True
        data['nx'] = nx
        data['ny'] = ny
            
    if grid == 'random':
        
        log.info("  grid type: random")
        
        xs = numpy.random.uniform(x1, x2, nx*ny)
        
        if ny > 1:
            
            ys = numpy.random.uniform(y1, y2, nx*ny)
            
        else:
            
            ys = [y1]
        
        data['grid'] = False
        
    data['x'] = xs
    data['y'] = ys
    
    function = fields[field]
    value = data['value']
    
    for i, coordinates in enumerate(zip(data['x'], data['y'], data['z'])):
        
        x, y, z = coordinates
        
        for prism in prisms:        
                        
            value[i] += function(prism['value'], 
                                 prism['x1'], prism['x2'], 
                                 prism['y1'], prism['y2'], 
                                 prism['z1'], prism['z2'], 
                                 float(x), float(y), float(z))
            
    log.info("  data points = %d" % (len(data['value'])))
    
    return data


def from_spheres(spheres, grid, field='gz'):
    """
    Create synthetic gravity data from a model made of spheres.

    The ``'value'`` key in *grid* will be filled with the generated gravity data
    **IN PLACE**!

    Parameters:

    * spheres
        List of spheres in the model. (see :func:`fatiando.geometry.sphere`)

    * grid
        A grid data type on which the gravitational effect will be calculated.
        *grid* MUST have a *z* coordinate set. (see :mod:`fatiando.grid`)

    * field
        What component of the gravity field to calculate. Can be any one of
        ``'gz'``, ``'gxx'``, ``'gxy'``, ``'gxz'``, ``'gyy'``, ``'gyz'``,
        ``'gzz'``

    """

    fields = {'gz':fatiando.grav.sphere.gz,
              'gxx':fatiando.grav.sphere.gxx,
              'gyy':fatiando.grav.sphere.gyy,
              'gzz':fatiando.grav.sphere.gzz}

    assert field in fields.keys(), "Invalid gravity field '%s'" % (field)

    assert 'x' in grid, "Invalid grid. Missing 'x' key."
    
    assert 'y' in grid, "Invalid grid. Missing 'y' key."
    
    assert 'z' in grid, "Invalid grid. Missing 'z' key."

    start = time.time()
    
    log.info("Generating synthetic %s data a sphere model:" % (field))
    log.info("  number of spheres = %d" % (len(spheres)))
    log.info("  data points = %d" % (len(grid['x'])))

    function = fields[field]
    
    data = numpy.zeros_like(grid['x'])

    for i, coordinates in enumerate(zip(grid['x'], grid['y'], grid['z'])):

        x, y, z = coordinates

        for sphere in spheres:
            
            data[i] += function(sphere['density'], sphere['radius'],
                                sphere['xc'], sphere['yc'], sphere['zc'], x, y,
                                z)

    grid['value'] = data
# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 3
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, see <http://www.gnu.org/licenses/>
#
# ##### END GPL LICENSE BLOCK #####

from setuptools import setup, find_packages

__author__ = "Sergi Blanch-Torne"
__copyright__ = "Copyright 2014, CELLS / ALBA Synchrotron"
__license__ = "GPLv3+"

# The version is updated automatically with bumpversion
# Do not update manually
__version = '1.0.0'


setup(
    name="ctdimfp",
    license=__license__,
    version=__version,
    author="Sergi Blanch-Torn\'e",
    author_email="sblanch@cells.es",
    packages=find_packages(),
    package_dir={'widgets': ['widgets/ui']},
    package_data={'widgets': ['*.ui']},
    entry_points={
        'console_scripts': [],
        'gui_scripts': [
            'ctdimfp = ctdimfp.MeasuredFillingPatternGui:main',
            ]
        },
    options={
        'build_scripts': {
                'executable': '/usr/bin/env python',
                    },
        },
    include_package_data=True,
    description="Graphical User Interface for the Alba's synchrotron "
                "Measured Filling Pattern Control",
    long_description="Graphical User Interface for the Alba's synchrotron "
                     "Measured Filling Pattern. The input information may "
                     "come from a tango device that collects information "
                     "from a photomutiplier read by a PicoHarp300 of from "
                     "a reading from an oscilloscope.",
    classifiers=['Development Status :: 5 - Production',
                 'Intended Audience :: Science/Research',
                 'License :: OSI Approved :: '
                 'GNU General Public License v3 or later (GPLv3+)',
                 'Programming Language :: Python',
                 'Topic :: Scientific/Engineering :: '
                 ''],
    url="https://github.com/srgblnch/MeasuredFillingPattern.git",
)

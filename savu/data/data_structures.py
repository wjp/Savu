# -*- coding: utf-8 -*-
# Copyright 2014 Diamond Light Source Ltd.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
.. module:: data_structures
   :platform: Unix
   :synopsis: Contains the Data class and all the data structures from which
   Data can inherit.

.. moduleauthor:: Nicola Wadeson <scientificsoftware@diamond.ac.uk>

"""

import sys
import logging
import warnings

import numpy as np

from savu.data.meta_data import MetaData


class Data(object):
    """
    The Data class dynamically inherits from relevant data structure classes
    at runtime and holds the data array.
    """

    def __init__(self, name, exp):
        self.meta_data = MetaData()
        pattern_list = self.set_available_pattern_list()
        self.meta_data.set_meta_data("pattern_list", pattern_list)
        self.name = name
        self.backing_file = None
        self.data = None
        self._plugin_data_obj = None
        self.exp = exp

    def set_plugin_data(self, plugin_data_obj):
        self._plugin_data_obj = plugin_data_obj

    def clear_plugin_data(self):
        self._plugin_data_obj = None

    def get_plugin_data(self):
        if self._plugin_data_obj is not None:
            return self._plugin_data_obj
        else:
            raise Exception("There is no PluginData object associated with "
                            "the Data object.")

    def get_transport_data(self, transport):
        transport_data = "savu.data.transport_data." + transport + \
                         "_transport_data"
        return self.import_class(transport_data)

    def import_class(self, class_name):
        name = class_name
        mod = __import__(name)
        components = name.split('.')
        for comp in components[1:]:
            mod = getattr(mod, comp)
        temp = name.split('.')[-1]
        module2class = ''.join(x.capitalize() for x in temp.split('_'))
        return getattr(mod, module2class.split('.')[-1])

    def __deepcopy__(self, memo):
        return self

    def add_base(self, ExtraBase):
        cls = self.__class__
        self.__class__ = cls.__class__(cls.__name__, (cls, ExtraBase), {})
        ExtraBase().__init__()

    def add_base_classes(self, bases):
        for base in bases:
            self.add_base(base)

    def set_shape(self, shape):
        self.meta_data.set_meta_data('shape', shape)

    def get_shape(self):
        shape = self.meta_data.get_meta_data('shape')
        try:
            dirs = self.meta_data.get_meta_data("fixed_directions")
            shape = list(shape)
            for ddir in dirs:
                shape[ddir] = 1
            shape = tuple(shape)
        except KeyError:
            pass
        return shape

    def set_dist(self, dist):
        self.meta_data.set_meta_data('dist', dist)

    def get_dist(self):
        return self.meta_data.get_meta_data('dist')

    def set_data_params(self, pattern, chunk_size, **kwargs):
        self.set_current_pattern_name(pattern)
        self.set_nFrames(chunk_size)

    def set_available_pattern_list(self):
        pattern_list = ["SINOGRAM",
                        "PROJECTION",
                        "VOLUME_YZ",
                        "VOLUME_XZ",
                        "VOLUME_XY",
                        "SPECTRUM",
                        "DIFFRACTION",
                        "CHANNEL",
                        "SPECTRUM_STACK",
                        "1D_METADATA"]
                        # added spectrum adp 17th August,
                        # Added diffraction 28th August adp
        return pattern_list

    def get_available_pattern_list(self):
        return self.meta_data.get_meta_data("pattern_list")

    def add_pattern(self, dtype, **kargs):
        if dtype in self.get_available_pattern_list():
            for args in kargs:
                self.meta_data.set_meta_data(["data_patterns", dtype, args],
                                             kargs[args])
        else:
            errorMsg = "The data pattern " + dtype + " does not exist. " + \
                       " Please choose from the following list: \n" + \
                       str(self.get_available_pattern_list())
            sys.exit(errorMsg)

    def add_volume_patterns(self):
        self.add_pattern("VOLUME_YZ", core_dir=(1, 2), slice_dir=(0,))
        self.add_pattern("VOLUME_XZ", core_dir=(0, 2), slice_dir=(1,))
        self.add_pattern("VOLUME_XY", core_dir=(0, 1), slice_dir=(2,))

    def set_direction_parallel_to_rotation_axis(self, tdir):
        self.check_direction(tdir, 'parallel_to_rotation_axis')
        self.set_main_axis(tdir, 'PROJECTION')

    def set_direction_perp_to_rotation_axis(self, tdir):
        self.check_direction(tdir, 'perp_to_rotation_axis')
        self.set_main_axis(tdir, 'SINOGRAM')

    def check_direction(self, tdir, dname):
        if not isinstance(tdir, int):
            raise TypeError('The should be an integer.')

        patterns = self.meta_data.get_meta_data("data_patterns")
        if not patterns:
            raise Exception("Please add available patterns before setting the"
                            " direction ", dname)

    def set_main_axis(self, tdir, pname):
        try:
            self.meta_data.get_meta_data(['data_patterns', pname])
            self.meta_data.set_meta_data(['data_patterns', pname, 'main_dir'],
                                         tdir)
        except KeyError:
            warnings.warn('The main_dir ' + str(tdir) + ' cannot be associated'
                          ' with the pattern ' + str(pname) + ' as it does not'
                          ' exist. ')

    def get_patterns(self):
        return self.meta_data.get_meta_data("data_patterns")

    def copy_patterns(self, patterns):
        self.meta_data.set_meta_data("data_patterns", patterns)


class PluginData(object):

    def __init__(self, data_obj):
        self.data_obj = data_obj
        self.data_obj.set_plugin_data(self)
        self.meta_data = MetaData()
        self.padding = None

    def get_total_frames(self):
        temp = 1
        slice_dir = \
            self.get_patterns()[self.get_pattern_name()]["slice_dir"]
        for tslice in slice_dir:
            temp *= self.get_shape()[tslice]
        return temp

    def set_pattern_name(self, name):
        self.meta_data.set_meta_data("name", name)
        self.check_data_type_exists()

    def get_pattern_name(self):
        name = self.meta_data.get_meta_data("name")
        if name is not None:
            return name
        else:
            raise Exception("The pattern name has not been set.")

    def get_pattern(self):
        pattern_name = self.get_pattern_name()
        return {pattern_name: self.get_patterns()[pattern_name]}

    def get_shape(self):
        return self.get_sub_shape(self.get_pattern_name())

    def check_dimensions(self, indices, core_dir, slice_dir, nDims):
        if len(indices) is not len(slice_dir):
            sys.exit("Incorrect number of indices specified when accessing "
                     "data.")

        if (len(core_dir)+len(slice_dir)) is not nDims:
            sys.exit("Incorrect number of data dimensions specified.")

    def check_data_type_exists(self):
        if self.get_pattern_name() not in \
                self.data_obj.get_available_pattern_list():
            raise Exception(("Error: The Data class does not contain an \
                        instance of ", self.get_pattern_name()))

    def get_slice_directions(self):
        try:
            [fix_dirs, value] = self.get_fixed_directions()
        except KeyError:
            fix_dirs = []
        slice_dirs = \
            self.data_obj.get_patterns()[self.get_pattern_name()]['slice_dir']
        to_slice = set(list(slice_dirs)).symmetric_difference(set(fix_dirs))
        temp = self.non_negative_directions(tuple(to_slice))
        return temp

    def get_core_directions(self):
        core_dir = \
            self.data_obj.get_patterns()[self.get_pattern_name()]['core_dir']
        return self.non_negative_directions(core_dir)

    def set_fixed_directions(self, dims, values):
        slice_dirs = self.get_slice_directions()
        for dim in dims:
            if dim in slice_dirs:
                self.meta_data.set_meta_data("fixed_directions", dims)
                self.meta_data.set_meta_data("fixed_directions_values", values)
            else:
                raise Exception("You are trying to fix a direction that is not"
                                " a slicing direction")

    def get_fixed_directions(self):
        try:
            fixed = self.meta_data.get_meta_data("fixed_directions")
            values = self.meta_data.\
                get_meta_data("fixed_directions_values")
        except KeyError:
            fixed = []
            values = []
        return [fixed, values]

    def delete_fixed_directions(self):
        try:
            del self.meta_data.dict["fixed_directions"]
            del self.meta_data.dict["fixed_directions_values"]
        except KeyError:
            pass

    def non_negative_directions(self, ddirs):
        nDims = len(self.data_obj.get_shape())
        index = [i for i in range(len(ddirs)) if ddirs[i] < 0]
        list_ddirs = list(ddirs)
        for i in index:
            list_ddirs[i] = nDims + ddirs[i]
        index = tuple(list_ddirs)
        return index

    def set_frame_chunk(self, nFrames):
        # number of frames to process at a time
        self.meta_data.set_meta_data("nFrames", nFrames)

    def get_frame_chunk(self):
        return self.meta_data.get_meta_data("nFrames")

    def get_index(self, indices):
        shape = self.get_shape()
        nDims = len(shape)
        name = self.get_current_pattern_name()
        ddirs = self.meta_data.get_meta_data("data_patterns")
        core_dir = ddirs[name]["core_dir"]
        slice_dir = ddirs[name]["slice_dir"]

        self.check_dimensions(indices, core_dir, slice_dir, nDims)

        index = [slice(None)]*nDims
        count = 0
        for tdir in slice_dir:
            index[tdir] = slice(indices[count], indices[count]+1, 1)
            count += 1

        return tuple(index)

    def get_sub_shape(self, name):
        core_dir = self.get_core_directions()
        shape = []
        for core in core_dir:
            shape.append(self.data_obj.get_shape()[core])
        return tuple(shape)

    def plugin_data_setup(self, **kwargs):
        if len(kwargs) is 2:
            self.in_data_setup(**kwargs)
        elif len(kwargs) is 3:
            self.out_data_setup(**kwargs)
        else:
            raise Exception("Incorrect number of arguments passed to "
                            "plugin_data_setup()")

    def in_data_setup(self, **kwargs):
        try:
            self.set_pattern_name(kwargs['pattern_name'])
            self.set_frame_chunk(kwargs['chunk'])
        except KeyError:
            raise Exception("When calling in_data_setup(), pattern_name and "
                            "chunk are required as kwargs.")

    def out_data_setup(self, **kwargs):
        try:
            self.set_pattern_name(kwargs['pattern_name'])
            self.set_frame_chunk(kwargs['chunk'])
            self.data_obj.set_shape(kwargs['shape'])
        except KeyError:
            raise Exception("When calling out_data_setup(), pattern_name, "
                            "shape and chunk are required as kwargs.")


class TomoRaw(object):

    def __init__(self):
        self.image_key = None
        self.image_key_slice = None
        self.frame_list = []

    def set_image_key(self, image_key):
        self.image_key = image_key
        self.set_image_key_slice()

    def get_image_key(self):
        try:
            return self.image_key[...]
        except:
            return None

    def set_frame_list(self, start, end):
        self.frame_list = [start, end]

    def set_image_key_slice(self):
        image_key_bool = self.get_image_key() == 0
        image_key_index = np.where(image_key_bool)[0]
        start = image_key_index[0]
        end = image_key_index[-1]
        self.set_frame_list(start, end)
        self.image_key_slice = slice(start, end + 1, 1)

    def get_image_key_slice(self):
        return self.image_key_slice

    def remove_dark_and_flat(self):
        if self.get_image_key() is not None:
            shape = self.get_shape()
            image_key = self.get_image_key()
            new_shape = shape[0] - len(image_key[image_key != 0])
            return (new_shape, shape[1], shape[2])
        else:
            logging.warn("Error in remove_dark_and_flat(): No image_key found")
            shape = self.get_shape()
            return (shape, shape[1], shape[2])

    def get_frame_raw(self, slice_list):
        pattern = self.get_current_pattern_name()
        image_slice = self.get_image_key_slice()
        new_slice_list = []
        if pattern is "SINOGRAM":
            for sl in slice_list:
                sl = list(sl)
                sl[0] = image_slice
                sl = tuple(sl)
                new_slice_list.append(sl)
        elif pattern is "PROJECTION":
            new_slice_list = slice_list[self.frame_list[0]:self.frame_list[1]]
        else:
            raise Exception("The pattern", pattern, " is not recognized \
                             by", self.__name__)

        return new_slice_list


class Padding(object):

    def __init__(self, pattern):
        self.padding_dirs = {}
        self.pattern_name = pattern.keys()[0]
        self.pattern = pattern[self.pattern_name]
        self.dims = self.set_dims()

    def set_dims(self):
        dims = []
        for key in self.pattern.keys():
            temp = self.pattern[key]
            for dim in (temp,) if type(temp) is int else temp:
                dims.append(int(dim))
        dims = list(set(dims))
        return dims

    def pad_frame_edges(self, padding):
        core_dirs = self.pattern['core_dir']
        for core in core_dirs:
            self.pad_direction([core, padding])

    def pad_multi_frames(self, padding):
        try:
            main_dir = self.pattern['main_dir']
        except KeyError:
            raise Exception('There is no main_dir associated with this '
                            'pattern')
        self.pad_direction([main_dir, padding])

    def pad_direction(self, pad_list):
        pdir = pad_list[0]
        padding = pad_list[1]
        if pdir not in self.dims:
            warnings.warn('Dimension ' + str(pdir) + ' is not associated '
                          ' with the pattern ' + self.pattern_name, +
                          '. IGNORING!')
        elif pdir in self.padding_dirs:
            warnings.warn('Padding.add_dir(): The direction ' + str(pdir) +
                          ' has already been added to the padding list.')
        else:
            self.padding_dirs[pdir] = padding

    def get_padding_directions(self):
        return self.padding_dirs

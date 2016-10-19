#  -*- coding: utf-8 -*-
# *********************************************************************
# plankton - a library for creating hardware device simulators
# Copyright (C) 2016 European Spallation Source ERIC
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
# *********************************************************************

import importlib


class Adapter(object):
    protocol = None

    def __init__(self, device, arguments=None):
        super(Adapter, self).__init__()
        self._device = device

    def start_server(self):
        pass

    def handle(self, cycle_delay=0.1):
        pass


def is_adapter(obj):
    try:
        return issubclass(obj, Adapter) and not obj.__module__.startswith('adapters')
    except TypeError:
        return False


def get_available_adapters(device_name, device_package):
    """
    This helper function returns a dictionary with name/type pairs. It imports the module
    device_package.device_name.adapters and puts those members of the module that inherit
    from Adapter into the dictionary.

    :param device_name: Device name for which to get the adapters.
    :param device_package: Name of the package where devices are defined.
    :return: Dictionary of name/type pairs for available adapters for that device.
    """
    adapters = dict()

    try:
        adapter_module = importlib.import_module('{}.{}.{}'.format(device_package, device_name, 'interfaces'))
        module_members = {member: getattr(adapter_module, member) for member in dir(adapter_module)}

        for name, member in module_members.items():
            if is_adapter(member):
                adapters[name] = member
    except ImportError:
        pass

    device_module = importlib.import_module('{}.{}'.format(device_package, device_name))

    for member in dir(device_module):
        member_object = getattr(device_module, member)

        if is_adapter(member_object):
            adapters[member] = member_object

    return adapters


def import_adapter(device_name, protocol_name, device_package='devices'):
    """
    This function tries to import an adapter for the given device that implements
    the requested protocol. If no adapter for that protocol exists, an exception
    is raised. If protocol name is None, the function returns an
    unspecified adapter. If no adapters are found at all, an error is raised.

    :param device_name: Name of device for which an adapter is requested.
    :param protocol_name: Requested protocol implemented by adapter.
    :param device_package: Name of the package where devices are defined.
    :return: Adapter class that implements requested protocol for the specified device.
    """
    available_adapters = get_available_adapters(device_name, device_package)

    if not protocol_name:
        return list(available_adapters.values())[0]

    for adapter in available_adapters.values():
        if adapter.protocol == protocol_name:
            return adapter

    raise RuntimeError(
        'No suitable adapter found for device \'{}\' and protocol \'{}\'.'.format(device_name, protocol_name))


class ForwardProperty(object):
    def __init__(self, target_member, property_name):
        """
        This is a small helper class that can be used to act as
        a forwarding property to relay property setting/getting
        to a member of the class it's installed on.

        Typical use would be:

            a = Foo()
            a._b = Bar() # Bar has property baz

            type(a).forward = ForwardProperty('_b', 'baz')

            a.forward = 10 # equivalent to a._b.baz = 10

        Note that this modifies the type Baz. Usage must thus be
        limited to cases where this type modification is
        acceptable.

        :param target_member: Target member to forward to.
        :param prop: Property of target to access.
        """
        self._target_member = target_member
        self._prop = property_name

    def __get__(self, instance, type=None):
        """
        This method forwards property read access on instance
        to the member of instance that was selected in __init__.

        :param instance: Instance of type.
        :param type: Type.
        :return: Attribute value of member property.
        """
        return getattr(getattr(instance, self._target_member), self._prop)

    def __set__(self, instance, value):
        """
        This method forwards property write access on instance
        to the member of instance that was selected in __init__.

        :param instance: Instance of type.
        :param value: Type.
        """
        setattr(getattr(instance, self._target_member), self._prop, value)


class ForwardMethod(object):
    def __init__(self, target, method):
        self._target = target
        self._method = method

    def __call__(self, *args, **kwargs):
        return getattr(self._target, self._method)(*args, **kwargs)

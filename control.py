#!/usr/bin/env python
import ast
import argparse
from core.control_client import ControlClient


def list_objects(remote):
    for obj in remote.keys():
        print(obj)


def show_api(remote, object_name):
    if not object_name in remote.keys():
        raise RuntimeError(
            'Object \'{}\' is not exposed by remote. Use -l to get a list of objects.'.format(object_name))

    obj = remote[object_name]

    properties = list(obj._properties)
    methods = []

    for member_name in dir(obj):
        if not member_name[0] in ('_', ':'):
            member = getattr(obj, member_name)

            if callable(member):
                methods.append(member_name)

    print('Type: {}'.format(type(obj).__name__))
    print('Properties:')
    for prop in sorted(properties):
        print('\t{}'.format(prop))
    print('Methods:')
    for method in sorted(methods):
        print('\t{}'.format(method))


def convert_type(value):
    try:
        return ast.literal_eval(value)
    except ValueError:
        return value


def call_method(remote, object_name, method, arguments):
    if not method:
        raise RuntimeError('Missing object member. Use -a to get a list of members.')

    attr = getattr(remote[object_name], method)
    args = [convert_type(arg) for arg in arguments]

    if callable(attr):
        return attr(*args)
    else:
        if not arguments:
            return attr
        else:
            setattr(remote[object_name], method, *args)


parser = argparse.ArgumentParser(
    description='A client to manipulate the simulated device remotely through a separate channel. The simulation must be started with the --rpc-host option.')
parser.add_argument('-r', '--rpc-host', default='127.0.0.1:10000',
                    help='HOST:PORT string specifying control server to connect to.')
parser.add_argument('-n', '--print-none', action='store_true',
                    help='Print None return value.')
parser.add_argument('object', nargs='?', default=None, help='Object to control. If left out, all objects are listed.')
parser.add_argument('member', nargs='?', default=None,
                    help='Object-member to access. If omitted, API of the object is listed.')
parser.add_argument('arguments', nargs='*',
                    help='Arguments to method call. For setting a property, supply the property value. ')

args = parser.parse_args()

remote = ControlClient(*args.rpc_host.split(':')).get_object_collection()

if not args.object:
    list_objects(remote)
else:
    if not args.member:
        show_api(remote, args.object)
    else:
        response = call_method(remote, args.object, args.member, args.arguments)

        if response is not None or args.print_none:
            print(response)

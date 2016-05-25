from __future__ import absolute_import, division, print_function, with_statement


import inspect
import sys

from turbo.util import import_object, camel_to_underscore
from turbo.log import helper_log


class _HelperObjectDict(dict):

    # def __setitem__(self, name, value):
    #     return super(_HelperObjectDict, self).setdefault(name, value)

    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError:
            raise


def install_helper(installing_helper_list, package_space):
    """ import {m : _HelperObjectDict() } in 'helpers' namespace.

    :param installing_helper_list:
    :param package_space:
    :return:
    """
    for item in installing_helper_list:
        # db model package
        package = import_object('.'.join(['helpers', item]), package_space)
        package_space[item] = _HelperObjectDict()
        # all py files  included by package
        all_modules = getattr(package, '__all__', [])
        for m in all_modules:
            try:
                module = import_object('.'.join(['helpers', item, m]), package_space)
            except Exception as e:
                helper_log.error('module helpers.%s.%s Import Error'%(item, m), exc_info=True)
                sys.exit(0)

            for cls_name in getattr(module, 'MODEL_SLOTS', []):
                cls = getattr(module, cls_name, None)
                if cls:
                    camel_name = cls.__name__
                    underscore_name = camel_to_underscore(camel_name)

                    package_space[item][camel_name] = cls
                    package_space[item][underscore_name] = cls()

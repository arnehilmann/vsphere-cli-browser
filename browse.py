#!/usr/bin/env python
"""
usage:
    browse HOST [--username=USERNAME] [--passwordfile=FILE]
"""

import atexit
import getpass
import re
import traceback

from pyVim import connect
from docopt import docopt

class VccBrowser(object):

    def __init__(self,
                 host,
                 username=getpass.getuser(),
                 password=None,
                 port=443):
        self.host = host
        if not password:
            password = getpass.getpass()
        si = connect.SmartConnect(host=host,
                                  user=username,
                                  pwd=password,
                                  port=443)
        atexit.register(connect.Disconnect, si)
        self.content = si.RetrieveContent()
        self._init_path()

    def _init_path(self):
        self.path = [(self.host, self.content.rootFolder)]

    @property
    def actual(self):
        return self.path[-1]

    def _render_breadcrumbs(self):
        breadcrumbs = []
        for item in self.path:
            breadcrumbs.append(item[0])
#            else:
#                breadcrumbs.append(str(item))
        return " > ".join(breadcrumbs)

    def _get_selections(self):
        actual = self.actual[1]
        fields = []
        if hasattr(actual, "append"):
            for key, value in enumerate(actual):
                if hasattr(value, "name"):
                    fields.append((key, value.name))
        try:
            actual.childEntity[0].name
            fields.append(("childEntity", "children"))
        except:
            pass
        if not fields:
            for field in dir(actual):
                if re.match("[a-z]", field) and field not in ["name", "parent", "permission", "tag", "value", "summary"]:
                    fields.append((field, field))
        return fields


    def _render_selections(self, selections):
        for nr, entry in enumerate(selections):
            _, value = entry
            print "%6i %s" % (nr + 1, value)

    def _render_node(self):
        actual = self.actual[1]
        if hasattr(actual, "summary"):
            print actual.summary

    def usage(self):
        print "[1]..[n]: select item, [..] back one level, [/] top level, [q] quit"

    def navigate(self):
        while True:
            try:
                print
                actual = self.actual[1]
                selections = None
                try:
                    self._render_node()
                    print self._render_breadcrumbs()
                    selections = self._get_selections()
                    self._render_selections(selections)
                except Exception:
                    traceback.print_exc()
                    print dir(actual)

                input = raw_input("--> ")
                if input in ["b", ".."]:
                    self.path.pop()
                    continue
                if input in ["t", "/"]:
                    self._init_path()
                    continue
                if input == "q":
                    break
                try:
                    nr = int(input)
                except:
                    self.usage()
                    continue

                key, value = selections[nr - 1]
                try:
                    selected = actual[int(key)]
                except:
                    selected = getattr(actual, key)
                #self.path.pop()
                self.path.append((value, selected))
            except Exception:
                traceback.print_exc()
                print "trying to continue"


if __name__ == "__main__":
    arguments = docopt(__doc__)

    pw_filename = arguments["--passwordfile"]
    password = None
    if pw_filename:
        with open(pw_filename) as pw_file:
            password = pw_file.read().strip()

    vvc = VccBrowser(host=arguments["HOST"],
                     username=arguments["--username"],
                     password=password)

    vvc.navigate()

#!/usr/bin/env python
#
# dependents.py - windows script to walk the dll dependency tree
#                 and search for missing libraries.
#
# author: richard.t.jones at uconn.edu
# version: may 10, 2024
#
# Notes:
# 1. Make sure that the MSVS utiility dumpbin.exe is
#    visible in your PATH before running this script.
# 2. I found that executables may have hundreds of
#
#    dependent dlls that I cannot find in my PATH, but
#    somehow the system knows where they are or else
#    knows to ignore them because the executable runs
#    fine anyway. In the code below I attempt to 
#    hide the common offenders of this type by only
#    printing names that do not begin with api- or
#    ext-, common instances that I cannot find in
#    my path, but their absence seems benign.

import re
import os
import sys
import subprocess

def usage():
    print("usage: dependents <binary>")
    sys.exit(1)

if len(sys.argv) != 2:
    usage()

def find_dll(dll):
    for dir in os.environ["PATH"].split(';'):
        if os.path.exists(os.path.join(dir, dll)):
            #print("found", dll, "in", dir)
            found_dlls[dll] = 1
            inspect(os.path.join(dir, dll))
            return 0
    if dll[:4] != "api-" and dll[:4] != "ext-":
        print("failed to find", dll, "in path")
    missing_dlls[dll] = 1
    return 1

def inspect(bin):
    res = subprocess.Popen(["dumpbin", "/dependents", bin],
                           stdout=subprocess.PIPE)
    for line in res.communicate()[0].decode().split('\n'):
        dll = line.strip(' ').rstrip()
        if len(dll.split()) == 1 and dll[-4:] == ".dll":
            if dll in found_dlls:
                found_dlls[dll] += 1
            elif dll in missing_dlls:
                missing_dlls[dll] += 1
            else:
                find_dll(dll)

found_dlls = {}
missing_dlls = {}
inspect(sys.argv[1])
print("Totals:", len(found_dlls), "found,", len(missing_dlls), "missing")

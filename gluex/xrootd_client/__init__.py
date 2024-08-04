#!/usr/bin/env python3
#
# This module finds a release of the XRootD client that was bundled with
# one of the gluex.hddm_X modules, unpacks it if necessary, and loads it
# into this namespace for use in the same session as the hddm_X module.
#
# author: richard.t.jones at uconn.edu
# version: august 3, 2024

import os
import sys
import glob
import subprocess

host_module = ""
try:
    if gluex.hddm_r:
        host_module = "hddm_r"
except:
    pass
try:
    if gluex.hddm_s:
        host_module = "hddm_s"
except:
    pass

gluex = '/'.join(__file__.split('/')[:-2])
tarballs = glob.glob(f"{gluex}/{host_module}/sharedlibs.tar.gz")
if len(tarballs) == 0:
    print("Error - no gluex xrootd module loaded, import one of gluex.hddm_* first.")

site_packages = glob.glob(f"{gluex}/xrootd_client/{host_module}/lib/python3.*/site-packages")
if len(site_packages) == 0:
    libdir = f"{gluex}/xrootd_client/{host_module}"
    os.mkdir(libdir)
    subprocess.run(["tar", "zxf", tarballs[0]], "-C", libdir)
    site_packages = glob.glob(f"{libdir}/lib/python3.*/site-packages")
    if len(site_packages) == 0:
        print("Error - unable to unpack the xrootd_client module, please contact the module author.")

sys.path.insert(0, site_packages[0])

from pyxrootd.client import *

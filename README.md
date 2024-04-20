# hddm_s - i/o library for reading and writing simulated events from the GlueX detector

The hddm_s module is a python wrapper around the c++ library that implements reading 
and writing of simulated events from the GlueX detector, based on the HDDM event i/o
framework. Every hddm_s file consists of a plain-text header describing the structure
of the event data contained in the file in xml format known as a hddm template. After
the header follows compressed binary data describing the sequence of simulated events
contained in the file. All files with valid hddm_s events share a compatible template
indicated by the class="s" attribute in the first line of the file header. All such
files should be readable by this module if they are compliant with the HDDM standard.
For more details on the standard, see https://github.com/rjones30/HDDM.

For details on the hddm_s API, install hddm_s and type "pydoc hddm_s". Here is a 
quickstart example of an analysis tool that reads from hddm_s input files.

import hddm_s
import pyxrootd

for rec in hddm_s.istream("

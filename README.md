# hddm\_s - i/o library for reading and writing simulated events from the GlueX detector

The hddm\_s module is a python wrapper around the c++ library that implements reading 
and writing of simulated events from the GlueX detector, based on the HDDM event i/o
framework. Every hddm\_s file consists of a plain-text header describing the structure
of the event data contained in the file in xml format known as a hddm template. After
the header follows compressed binary data describing the sequence of simulated events
contained in the file. All files with valid hddm\_s events share a compatible template
indicated by the class="s" attribute in the first line of the file header. All such
files should be readable by this module if they are compliant with the HDDM standard.
For more details on the standard, see https://github.com/rjones30/HDDM.

For details on the hddm\_s API, install hddm\_s and type "pydoc hddm\_s". Here is a 
quickstart example of an analysis tool that reads from hddm\_s input files.

	import hddm\_s
	for rec in hddm_s.istream("http://nod25.phys.uconn.edu:2880/Gluex/simulation" +
	                          "/simsamples/particle_gun-v5.2.0/particle_gun001_019.hddm"):
	   for pe in rec.getPhysicsEvents():
	      print(f"http streaming reader found run {pe.runNo}, event {pe.eventNo}")
	
	for rec in hddm_s.istream("https://nod25.phys.uconn.edu:2843/Gluex/simulation" +
	                          "/simsamples/particle_gun-v5.2.0/particle_gun001_019.hddm"):
	   for pe in rec.getPhysicsEvents():
	      print(f"https streaming reader found run {pe.runNo}, event {pe.eventNo}")
	
	for rec in hddm_s.istream("root://nod25.phys.uconn.edu/Gluex/simulation" +
	                          "/simsamples/particle_gun-v5.2.0/particle_gun001_019.hddm"):
	   for pe in rec.getPhysicsEvents():
	      print(f"xrootd streaming reader run {pe.runNo}, event {pe.eventNo}")
	

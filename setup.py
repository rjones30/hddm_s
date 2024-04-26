import os
import re
import glob
import setuptools
from setuptools.command.build_ext import build_ext as build_ext
from setuptools.command.install_lib import install_lib as install_lib

templates = {
  "hddm_s": ["event.xml"],
}

sources = {
  "xerces-c.url": "https://github.com/apache/xerces-c.git",
  "xerces-c.tag": "tags/v3.2.5",
  "hdf5.url": "https://github.com/HDFGroup/hdf5.git",
  "hdf5.tag": "tags/hdf5-1_10_8",
#  "xrootd.url": "https://github.com/xrootd/xrootd.git",
#  "xrootd.tag": "tags/v5.6.9",
  "HDDM.url": "https://github.com/rjones30/HDDM.git",
  "HDDM.tag": "tags/4.30.1",
}

class CMakeExtension(setuptools.Extension):

    def __init__(self, name):
        super().__init__(name, sources=[])


class build_ext_with_cmake(build_ext):

    def run(self):
        for ext in self.extensions:
            self.build_with_cmake(ext)
        super().run()

    def build_with_cmake(self, ext):
        cwd = os.getcwd()
        if f"{ext.name}.url" in sources:
            if not os.path.isdir(ext.name):
                self.spawn(["git", "clone", sources[ext.name + ".url"]])
            os.chdir(ext.name)
            self.spawn(["git", "checkout", sources[ext.name + ".tag"]])
            os.chdir(cwd)
        else:
            return 0
            raise Exception("missing sources",
                            f"no package sources specified for {ext.name}")
        build_temp = f"build.{ext.name}"
        if not os.path.isdir(build_temp):
            os.mkdir(build_temp)
        config = "Debug" if self.debug else "Release"
        cmake_args = [
          f"-DCMAKE_INSTALL_PREFIX={os.path.abspath(cwd)}/build",
          f"-DCMAKE_BUILD_TYPE={config}",
        ]
        build_args = [
          "--config", config,
          "--", "-j4"
        ]
        os.chdir(build_temp)
        self.spawn(["cmake", f"../{ext.name}"] + cmake_args)
        if not self.dry_run:
            self.spawn(["cmake", "--build", "."] + build_args)
            self.spawn(["cmake", "--install", "."])
            os.chdir(cwd)
            self.spawn(["rm", "-rf", ext.name, f"build.{ext.name}"])
        os.chdir(cwd)
        if ext.name == "HDDM": # finish construction of the hddm module
            for module in templates:
                for model in templates[module]:
                    os.chdir(module)
                    self.spawn(["../build/bin/hddm-cpp", model])
                    self.spawn(["../build/bin/hddm-py", model])
                    self.spawn(["cp", f"py{module}.cpy", f"py{module}.cpp"])


class install_ext_solibs(install_lib):

    def run(self):
        super().run()
        for wheel in glob.glob("build/bdist.*/wheel"):
            for solib in os.listdir(wheel):
                for mext in re.finditer("^([^/]*).cpython.*", solib):
                    if not mext.group(1) in templates:
                        self.spawn(["rm", f"{wheel}/{solib}"])
 

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name = "hddm_s",
    version = "1.0.36",
    url = "https://github.com/rjones30/hddm_s",
    author = "Richard T. Jones",
    description = "i/o module for GlueX simulated events",
    long_description = long_description,
    long_description_content_type = "text/markdown",
    packages = templates.keys(),
    package_data = templates,
    classifiers = [
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],                                      # Information to filter the project on PyPi website
    python_requires = '>=3.6',              # Minimum version requirement of the package
    #packages = templates.keys(),           # Name of the python package
    install_requires = [                    # Install other dependencies if any
      "setuptools-git",
      "xrootd",
   ],
    ext_modules = [
      CMakeExtension("xerces-c"),
      CMakeExtension("hdf5"),
      #CMakeExtension("xrootd"),
      CMakeExtension("HDDM"),
      setuptools.Extension("hddm_s",
           include_dirs = [".", "../build/include"],
           library_dirs = ["../build/lib", "../build/lib64"],
           libraries = ["xstream", "bz2", "z", 
                        ":libhdf5_hl.a", ":libhdf5.a",
                       ],
           extra_compile_args = ["-std=c++11", "-DHDF5_SUPPORT"],
           sources = ["hddm_s++.cpp", "pyhddm_s.cpp"]),
    ],
    cmdclass = {
      "build_ext": build_ext_with_cmake,
      "install_lib": install_ext_solibs,
    }
)

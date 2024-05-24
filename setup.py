import os
import re
import glob
import shutil
import sysconfig

import setuptools
from setuptools.command.build_ext import build_ext as build_ext
from setuptools.command.install_lib import install_lib as install_lib

templates = {
  "hddm_s": ["event.xml"],
}

sources = {
  "zlib.url": "https://github.com/madler/zlib.git",
  "zlib.tag": "tags/v1.3.1",
  "bzip2.url": "https://github.com/rjones30/bzip2.git",
  "bzip2.tag": "",
  "xerces-c.url": "https://github.com/apache/xerces-c.git",
  "xerces-c.tag": "tags/v3.2.5",
  "hdf5.url": "https://github.com/HDFGroup/hdf5.git",
  "hdf5.tag": "tags/hdf5-1_10_8",
#  "xrootd.url": "https://github.com/xrootd/xrootd.git",
#  "xrootd.tag": "tags/v5.6.9",
  "pthread-win32.url": "https://github.com/GerHobbelt/pthread-win32.git",
  "pthread-win32.tag": "version-3.1.0-release",
  "HDDM.url": "https://github.com/rjones30/HDDM.git",
  "HDDM.tag": "",
}

class CMakeExtension(setuptools.Extension):

    def __init__(self, name):
        super().__init__(name, sources=[])


class build_ext_with_cmake(build_ext):

    def run(self):
        build_extension_solibs = []
        for ext in self.extensions:
            self.build_with_cmake(ext)
            if ext.name in templates:
                build_extension_solibs.append(ext)
        self.extensions = build_extension_solibs
        super().run()

    def build_with_cmake(self, ext):
        if "win" in ext.name and not "win" in sysconfig.get_platform():
            return 0
        cwd = os.getcwd()
        if f"{ext.name}.url" in sources:
            if not os.path.isdir(ext.name):
                self.spawn(["git", "clone", sources[ext.name + ".url"]])
            os.chdir(ext.name)
            tag = sources[ext.name + ".tag"]
            if tag:
                self.spawn(["git", "checkout", tag])
            os.chdir(cwd)
        else:
            return 0
            raise Exception("missing sources",
                            f"no package sources specified for {ext.name}")
        
        cmake_config = "Debug" if self.debug else "Release"
        build_args = ["--config", cmake_config]
        if shutil.which("cmake"):
            cmake = "cmake"
        else:
            # Only happens on Windows, try to install it
            self.spawn(["scripts/install_cmake.bat"])
            cmake = "cmake.exe"

        build_temp = f"build.{ext.name}"
        if not os.path.isdir(build_temp):
            os.mkdir(build_temp)
        os.chdir(build_temp)
        cmake_args = [
          f"-DCMAKE_INSTALL_PREFIX={os.path.abspath(cwd)}/build",
          f"-DEXTRA_INCLUDE_DIRS={os.path.abspath(cwd)}/build/include",
          f"-DCMAKE_BUILD_TYPE={cmake_config}",
          f"-DCMAKE_VERBOSE_MAKEFILE:BOOL=ON",
        ]
        if sysconfig.get_platform() == "win32":
            cmake_args += ["-A", "Win32"]
        self.spawn([cmake, f"../{ext.name}"] + cmake_args)
        if not self.dry_run:
            self.spawn([cmake, "--build", "."] + build_args + ["-j4"])
            self.spawn([cmake, "--install", "."])
            os.chdir(cwd)
            self.spawn(["rm", "-rf", ext.name, f"build.{ext.name}"])
        os.chdir(cwd)
        self.spawn(["ls", "-l", "-R", "build"])
        print("build target architecture is", sysconfig.get_platform())
        if ext.name == "HDDM": # finish construction of the hddm module
            if "win" in sysconfig.get_platform():
                if "PATH" in os.environ:
                    os.environ["PATH"] += ";../build/bin"
                else:
                    os.environ["PATH"] = "../build/bin"
            else:
                if "PATH" in os.environ:
                    os.environ["PATH"] += ":../build/bin"
                else:
                    os.environ["PATH"] = "../build/bin"
            for lib in glob.glob("build/lib*"):
                for ldpath in ["LD_LIBRARY_PATH", "DYLD_LIBRARY_PATH"]:
                    if ldpath in os.environ:
                        os.environ[ldpath] += f":{cwd}/{lib}"
                    else:
                        os.environ[ldpath] = f":{cwd}/{lib}"
            #os.environ["DYLD_PRINT_LIBRARIES"] = "1"
            #os.environ["DYLD_PRINT_LIBRARIES_POST_LAUNCH"] = "1"
            #os.environ["DYLD_PRINT_RPATHS"] = "1"
            for module in templates:
                for model in templates[module]:
                    os.chdir(module)
                    self.spawn(["hddm-cpp", model])
                    self.spawn(["hddm-py", model])
                    self.spawn(["cp", f"py{module}.cpy", f"py{module}.cpp"])
                    os.chdir(cwd)


class install_ext_solibs(install_lib):

    def run(self):
        super().run()
        for wheel in glob.glob("build/bdist.*/wheel"):
            for solib in os.listdir(wheel):
                for mext in re.finditer("^([^/]*).cpython.*", solib):
                    if not mext.group(1) in templates:
                        self.spawn(["rm", "-f", f"{wheel}/{solib}"])
 

with open("README.md", "r") as fh:
    long_description = fh.read()

if "win" in sysconfig.get_platform():
    extension_include_dirs = ["hddm_s", "build\\include"]
    extension_library_dirs = ["build\\lib",]
    extension_libraries = ["libhdf5_hl",
                           "libhdf5",
                           "xstream",
                           "bz2",
                           "zlibstatic",
                           "xerces-c_3",
                           "libpthreadVC3",
                           "ws2_32",
                          ]
else:
    extension_include_dirs = ["hddm_s", "build/include"]
    extension_library_dirs = ["build/lib", "build/lib64"]
    extension_libraries = ["build/lib/libhdf5_hl.a",
                           "build/lib/libhdf5.a",
                           "build/lib/libxstream.a",
                           "build/lib/libbz2.a",
                           "build/lib/libz.a",
                           "build/lib/libxerces-c.a",
                           "build/lib/libpthread.a",
                          ]
setuptools.setup(
    name = "hddm_s",
    version = "1.0.63",
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
    #install_requires = [                    # Install other dependencies if any
    #  "setuptools-git",
    #  "xrootd",
    #],
    ext_modules = [
      CMakeExtension("zlib"),
      CMakeExtension("bzip2"),
      CMakeExtension("xerces-c"),
      CMakeExtension("hdf5"),
      #CMakeExtension("xrootd"),
      CMakeExtension("pthread-win32"),
      CMakeExtension("HDDM"),
      setuptools.Extension("hddm_s",
           include_dirs = extension_include_dirs,
           library_dirs = extension_library_dirs,
           libraries = extension_libraries,
           extra_compile_args = ["-std=c++11", "-DHDF5_SUPPORT"],
           sources = ["hddm_s/hddm_s++.cpp", "hddm_s/pyhddm_s.cpp"]),
    ],
    cmdclass = {
      "build_ext": build_ext_with_cmake,
      "install_lib": install_ext_solibs,
    }
)

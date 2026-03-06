import os
import re
import sys
import glob
import shutil
import sysconfig
import stat
import time
import platform
import importlib.machinery

import setuptools
from setuptools.command.build_ext import build_ext as build_ext
from setuptools.command.install_lib import install_lib as install_lib

templates = {
  "gluex.hddm_s": ["gluex/hddm_s/event.xml"]
}

sources = {
  "zlib.url": "https://github.com/rjones30/zlib.git",
  "zlib.tag": "",
  "bzip2.url": "https://github.com/rjones30/bzip2.git",
  "bzip2.tag": "",
  "xerces-c.url": "https://github.com/rjones30/xerces-c.git",
  "xerces-c.tag": "",
  "hdf5.url": "https://github.com/HDFGroup/hdf5.git",
  "hdf5.tag": "tags/hdf5-1_12_3",
  "pthread-win32.url": "https://github.com/GerHobbelt/pthread-win32.git",
  "pthread-win32.tag": "version-3.1.0-release",
  "libuuid.url": "https://github.com/rjones30/libuuid.git",
  "libuuid.tag": "",
  "libxml2.url": "https://github.com/rjones30/libxml2.git",
  "libxml2.tag": "",
  "cpr.url": "https://github.com/rjones30/cpr.git",
  "cpr.tag": "",
  #"xrootd.url": "https://github.com/rjones30/xrootd.git",
  #"xrootd.tag": "stable-5.7.1-for-hddm",
  "xrootd.url": "https://github.com/xrootd/xrootd.git",
  "xrootd.tag": "v5.9.1",
  "HDDM.url": "https://github.com/rjones30/HDDM.git",
  "HDDM.tag": "main",
}

if "pypy" in platform.python_implementation().lower():
    python_impl = "pp"
else:
    python_impl = "cp"
python_tag = f"{python_impl}{sys.version_info[0]}{sys.version_info[1]}-{platform.machine()}"
BUILD_ROOT = os.path.join(os.getcwd(), f"build-{python_tag}")

def force_rm(func, path, _):
    """Platform-independent way to handle read-only files during rmtree."""
    os.chmod(path, stat.S_IWRITE)
    func(path)

class CMakeExtension(setuptools.Extension):

    def __init__(self, name):
        super().__init__(name, sources=[])


class build_ext_with_cmake(build_ext):

    def run(self):
        build_extension_solibs = []
        cwd = os.getcwd()
        for ext in self.extensions:
            print(f"NOTICE - building {ext.name} in {BUILD_ROOT}")
            self.build_with_cmake(ext)
            if "xrootd" in ext.name:
                if "win" in sysconfig.get_platform():
                    print(f">>> Skipping XRootD harvesting on Windows")
                else:
                    shlibs = glob.glob(os.path.join(BUILD_ROOT, "**", "*.so"), recursive=True) + \
                             glob.glob(os.path.join(BUILD_ROOT, "**", "*.pyd"), recursive=True)
                    for shlib in shlibs:
                        if os.path.basename(shlib).startswith("client"):
                            target_dir = os.path.join(self.build_lib, "gluex", "hddm_s", "pyxrootd")
                            print(f"NOTICE - saving {shlib} to target_dir {target_dir}")
                            shutil.copy2(shlib, target_dir)
            if ext.name in templates:
                build_extension_solibs.append(ext)
        self.extensions = build_extension_solibs

        super().run()
        time.sleep(0.2)

        hddm_dir = os.path.join(cwd, "gluex", "hddm_s")
        old_path = self.get_ext_fullpath("gluex.hddm_s")
        new_name = os.path.basename(old_path).replace("hddm_s", "__init__", 1)
        new_path = os.path.join(os.path.dirname(old_path), "hddm_s", new_name)
        if os.path.exists(old_path):
            os.makedirs(os.path.dirname(new_path), exist_ok=True)
            shutil.move(old_path, new_path)
            if hasattr(self, 'outputs'):
                self.outputs = [new_path if x == old_path else x for x in self.outputs]
        valid_suffixes = importlib.machinery.EXTENSION_SUFFIXES + [".xml", ".py"]
        keep = {"__init__.py", "pyxrootd", "hddm_s"}
        for f in os.listdir(hddm_dir):
            if f in keep:
                continue
            path = os.path.join(hddm_dir, f)
            if not any(f.endswith(s) for s in valid_suffixes):
                if os.path.isdir(path):
                    shutil.rmtree(path, onerror=force_rm)
                else:
                    os.remove(path)

    def build_with_cmake(self, ext):
        if "win" in ext.name and not "win" in sysconfig.get_platform():
            return 0
        elif "xrootd" in ext.name and "win" in sysconfig.get_platform():
            return 0
        elif ext.name[:3] == "lib" and "win" in sysconfig.get_platform():
            return 0
        elif os.getenv("SKIP_BUILD") == "1":
            print(f">>> Skipping actual build for {ext.name} (Dry Run Mode)")
            return 0
        cwd = os.getcwd()
        os.mkdir(BUILD_ROOT, exist_ok=True)
        if f"{ext.name}.url" in sources:
            if os.path.isdir(ext.name):
                shutil.rmtree(ext.name, onerror=force_rm)
                while os.path.isdir(ext.name):
                   time.sleep(0.1)
            os.chdir(BUILD_ROOT)
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
            cmake = ["cmake"]
        else:
            # Only happens on Windows, try to install it
            self.spawn(["scripts/install_cmake.bat"])
            cmake = ["cmake.exe"]
        build_temp = os.path.join(BUILD_ROOT, f"build.{ext.name}")
        os.mkdir(build_temp, exist_ok=True)
        os.chdir(build_temp)
        if "arm64" in sysconfig.get_platform():
            os.environ["ARCHFLAGS"] = "-arch arm64"
        cmake_args = [
            f"-DCMAKE_INSTALL_PREFIX={BUILD_ROOT}",
            f"-DEXTRA_INCLUDE_DIRS={BUILD_ROOT}/include",
            f"-DCMAKE_BUILD_TYPE={cmake_config}",
            f"-DCMAKE_POSITION_INDEPENDENT_CODE:BOOL=on",
            f"-DCMAKE_OSX_DEPLOYMENT_TARGET=10.15",
            f"-DCMAKE_VERBOSE_MAKEFILE:BOOL=on",
            f"-DCMAKE_PREFIX_PATH={BUILD_ROOT}/cmake",
            f"-DPython3_INCLUDE_DIR={sysconfig.get_path('include')}",
            f"-DPython3_EXECUTABLE={sys.executable}",
            f"-DPython3_ROOT_DIR={os.path.dirname(os.path.dirname(sys.executable))}",
            f"-DPython_EXECUTABLE={sys.executable}",
            f"-DPYTHON_EXECUTABLE={sys.executable}",
            f"-DPython_ROOT_DIR={os.path.dirname(os.path.dirname(sys.executable))}",
            f"-DPython_FIND_STRATEGY=LOCATION",
            f"-DENABLE_PYTHON=ON",
        ]
        if "arm64" in sysconfig.get_platform():
            cmake_args += ["-DCMAKE_OSX_ARCHITECTURES=arm64"]
        if sysconfig.get_platform() == "win32":
            cmake_args += ["-A", "Win32"]
        if "pypy" in sys.version.lower():
            cmake_args += ["-DIS_PYPY:BOOL=ON"]
        if "xrootd" in ext.name:
            cmake_args += [f"-DXRDCL_LIB_ONLY:bool=on"]
            cmake_args += [f"-DOPENSSL_INCLUDE_DIR:path={BUILD_ROOT}/include"]
            cmake_args += [f"-DCMAKE_CXX_FLAGS=-D_GLIBCXX_USE_CXX11_ABI=1 -Wabi-tag"]
            #cmake_args += ["--log-level=VERBOSE",                 # Tell CMake to be chatty
            #               "-DPython_FIND_DEBUG=ON",              # Special debug mode for the Python module
            #               "-DCMAKE_MESSAGE_INDENT_LEVEL=2",      # Make logs readable
            #               "-DCMAKE_MESSAGE_CONTEXT_SHOW=ON",     # Show where messages are coming from
            #              ]
        else:
            cmake_args += [f"-DBUILD_SHARED_LIBS:BOOL=off"]
        if "hdf5" in ext.name:
            cmake_args += [f"-DHDF5_SRC_INCLUDE_DIRS={BUILD_ROOT}/include"]
        if "HDDM" in ext.name:
            cmake_args += [f"-DHDF5_ROOT:PATH={BUILD_ROOT}"]
            if "win" in sysconfig.get_platform():
                cmake_args += [f"-DENABLE_ISTREAM_OVER_XROOTD:BOOL=off"]
        self.spawn(cmake + [f"../{ext.name}"] + cmake_args)
        if "xerces" in ext.name and sysconfig.get_platform() != "win32":
            for inc in glob.glob(os.path.join(BUILD_ROOT, "include", "uuid", "uuid.h")):
                self.spawn(["echo", "mv", inc, inc + "idden"])
                self.spawn(["mv", inc, inc + "idden"])
        if not self.dry_run:
            if "uuid" in ext.name or "win" in sysconfig.get_platform():
                self.spawn(cmake + ["--build", "."] + build_args)
            else:
                self.spawn(cmake + ["--build", "."] + build_args + ["-j4"])
            self.spawn(cmake + ["--install", "."])
            os.chdir(cwd)
            for solib in glob.glob(os.path.join(BUILD_ROOT, "lib", "*.so*")):
               self.spawn(["mkdir", "-p", os.path.join(BUILD_ROOT, "lib64")])
               shutil.copy2(solib, re.sub(r"[\\/]lib[\\/]", os.sep + "lib64" + os.sep, solib))
            for arlib in glob.glob(os.path.join(BUILD_ROOT, "lib64", "*.a")):
               self.spawn(["mkdir", "-p", os.path.join(BUILD_ROOT, "lib")])
               shutil.copy2(arlib, re.sub(r"[\\/]lib64[\\/]", os.sep + "lib" + os.sep, arlib))
            for arlib in glob.glob(os.path.join(BUILD_ROOT, "lib*", "*.a")):
               if re.match(r".*_static\.a$", arlib):
                  shutil.copy2(arlib, re.sub(r"_static\.a$", ".a", arlib))
               else:
                  shutil.copy2(arlib, re.sub(r"\.a$", "_static.a", arlib))
            shutil.rmtree(ext.name, ignore_errors=True)
            shutil.rmtree(build_temp, ignore_errors=True)
        os.chdir(cwd)
        print("build target architecture is", sysconfig.get_platform())
        if ext.name == "HDDM": # finish construction of the hddm module
            if "win" in sysconfig.get_platform():
                if "PATH" in os.environ:
                    os.environ["PATH"] += f";{BUILD_ROOT}/bin"
                else:
                    os.environ["PATH"] = f"{BUILD_ROOT}/bin"
            else:
                if "PATH" in os.environ:
                    os.environ["PATH"] += f":{BUILD_ROOT}/bin"
                else:
                    os.environ["PATH"] = f"{BUILD_ROOT}/bin"
            for lib in glob.glob(f"{BUILD_ROOT}/lib*"):
                for ldpath in ["LD_LIBRARY_PATH", "DYLD_LIBRARY_PATH"]:
                    if ldpath in os.environ:
                        os.environ[ldpath] += f"{os.pathsep}{cwd}/{lib}"
                    else:
                        os.environ[ldpath] = f"{cwd}/{lib}"
            #os.environ["DYLD_PRINT_LIBRARIES"] = "1"
            #os.environ["DYLD_PRINT_LIBRARIES_POST_LAUNCH"] = "1"
            #os.environ["DYLD_PRINT_RPATHS"] = "1"
            for module in templates:
                for model in templates[module]:
                    model_dir = os.path.dirname(model)
                    model_name = os.path.basename(model)
                    if model_dir:
                        os.chdir(model_dir)
                    self.spawn(["hddm-cpp", model_name])
                    self.spawn(["hddm-py", model_name])
                    modname = module.split('.')[-1]
                    shutil.copy2(f"py{modname}.cpy", f"py{modname}.cpp")
                    generated_helper = f"setup_{modname}.py"
                    if os.path.exists(generated_helper):
                        os.remove(generated_helper)
                    os.chdir(cwd)


with open("README.md", "r") as fh:
    long_description = fh.read()

if "win" in sysconfig.get_platform():
    extension_include_dirs = [os.path.join("gluex", "hddm_s"),
                              os.path.join(BUILD_ROOT, "include"),
                             ]
    extension_library_dirs = [os.path.join(BUILD_ROOT, "lib")]
    extension_libraries = ["libhdf5_hl",
                           "libhdf5",
                           "xstream",
                           "bz2",
                           "zlibstatic",
                           "xerces-c_3",
                           "libpthreadVC3",
                           "ws2_32",
                           "httpstream",
                           "cpr",
                           "libcurl",
                           "libssl",
                           "libcrypto",
                           "Advapi32",
                           "Crypt32",
                          ]
    extension_compile_args = ["-std:c++20",
                              "-DHDF5_SUPPORT",
                              "-DISTREAM_OVER_HTTP",
                             ]
else:
    extension_include_dirs = ["gluex/hddm_s",
                              f"{BUILD_ROOT}/include",
                              f"{BUILD_ROOT}/include/libxml2",
                              f"{BUILD_ROOT}/include/xrootd",
                             ]
    extension_library_dirs = [f"{BUILD_ROOT}/lib", f"{BUILD_ROOT}/lib64"]
    extension_libraries = ["hdf5_hl_static",
                           "hdf5_static",
                           "xstream",
                           "bz2_static",
                           "z_static",
                           "xerces-c_static",
                           "pthread",
                           "httpstream",
                           "cpr_static",
                           "curl_static",
                           "ssl_static",
                           "crypto_static",
                           "xrootdstream",
                           #"XrdCl_static",
                           #"XrdUtils_static",
                           #"XrdXml_static",
                           "XrdCl",
                           "XrdUtils",
                           "XrdXml",
                           "uuid_static",
                           "xml2_static",
                          ]
    extension_compile_args = ["-std=c++20",
                              "-DHDF5_SUPPORT",
                              "-DISTREAM_OVER_HTTP",
                              "-DISTREAM_OVER_XROOTD"
                             ]
if "macos" in sysconfig.get_platform():
    extension_compile_args += ["-mmacosx-version-min=10.15"]

ext_patterns = [f"*{s}" for s in importlib.machinery.EXTENSION_SUFFIXES]

setuptools.setup(
    packages = ["gluex.hddm_s", "gluex.hddm_s.pyxrootd"],
    #namespace_packages=['gluex'],
    package_data = {"gluex.hddm_s": ["event.xml"] + ext_patterns,
    },
    ext_modules = [
      CMakeExtension("zlib"),
      CMakeExtension("bzip2"),
      CMakeExtension("xerces-c"),
      CMakeExtension("hdf5"),
      CMakeExtension("pthread-win32"),
      CMakeExtension("libuuid"),
      CMakeExtension("libxml2"),
      CMakeExtension("cpr"),
      CMakeExtension("xrootd"),
      CMakeExtension("HDDM"),
      setuptools.Extension("gluex.hddm_s",
           include_dirs = extension_include_dirs,
           library_dirs = extension_library_dirs,
           libraries = extension_libraries,
           extra_compile_args = extension_compile_args,
           sources = ["gluex/hddm_s/hddm_s++.cpp",
                      "gluex/hddm_s/pyhddm_s.cpp"]
      ),
    ],
    cmdclass = {
      "build_ext": build_ext_with_cmake,
    }
)

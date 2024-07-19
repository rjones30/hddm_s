
with open("README.md", "r") as fh:
    long_description = fh.read()

if "win" in sysconfig.get_platform():
    extension_include_dirs = ["gluex\\hddm_s",
                              "build\\include",
                             ]
    extension_library_dirs = ["build\\lib"]
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
    extension_compile_args = ["-std:c++17",
                              "-DHDF5_SUPPORT",
                              "-DISTREAM_OVER_HTTP",
                             ]
else:
    extension_include_dirs = ["gluex/hddm_s",
                              "build/include",
                              "build/include/libxml2",
                              "build/include/xrootd",
                             ]
    extension_library_dirs = ["build/lib"]
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
                           "XrdCl_static",
                           "XrdUtils_static",
                           "XrdXml_static",
                           "uuid_static",
                           "xml2_static",
                          ]
    extension_compile_args = ["-std=c++17",
                              "-DHDF5_SUPPORT",
                              "-DISTREAM_OVER_HTTP",
                              "-DISTREAM_OVER_XROOTD"
                             ]
if "macos" in sysconfig.get_platform():
    extension_compile_args += ["-mmacosx-version-min=10.15"]

setuptools.setup(
    name = "gluex.hddm_s",
    version = "2.1.8",
    url = "https://github.com/rjones30/hddm_s",
    author = "Richard T. Jones",
    description = "i/o module for GlueX simulated events",
    long_description = long_description,
    long_description_content_type = "text/markdown",
    packages = templates.keys(),
    namespace_packages=['gluex'],
    package_data = templates,
    classifiers = [
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],                                      # Information to filter the project on PyPi website
    python_requires = '>=3.6',              # Minimum version requirement of the package
    #install_requires = [                   # Install other dependencies if any
    #  "setuptools-git",
    #],
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
      "install_lib": install_ext_solibs,
    }
)

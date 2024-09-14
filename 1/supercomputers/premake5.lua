paths = {
    vcpkg = "%{wks.location}/vcpkg_installed/x64-windows",
}

vcpkg = {
    include = "%{paths.vcpkg}/include",
    lib = { debug = "%{paths.vcpkg}/debug/lib", release = "%{paths.vcpkg}/lib"},
    bin = { debug = "%{paths.vcpkg}/debug/bin", release = "%{paths.vcpkg}/bin"},
}

workspace "supercomputers"
    architecture "x86_64"
    configurations { "Debug", "Release" }

include "labs-openmp"
include "labs-mpi"


workspace "supercomputers"
    architecture "x86_64"
    configurations { "Debug", "Release" }

include "labs-openmp"

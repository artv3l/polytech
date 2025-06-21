workspace "sp"
    architecture "x86_64"
    configurations { "Debug", "Release" }
    startproject "task1"

project "task1"
    kind "ConsoleApp"
    language "C++"
    cppdialect "C++17"

    files { "komppl.c" }

project "task2"
    kind "ConsoleApp"
    language "C++"
    cppdialect "C++17"

    files { "kompassr.c" }

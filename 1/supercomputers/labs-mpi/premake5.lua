project "labs-mpi"
    kind "ConsoleApp"
    language "C++"
    cppdialect "C++17"
    
    files { "**.hpp", "**.cpp" }

    includedirs {
        "%{vcpkg.include}",
    }

    links {
        "%{vcpkg.lib.debug}/msmpi.lib"
    }

    filter "configurations:Debug"
        defines { "DEBUG" }
        symbols "On"
        
    filter "configurations:Release"
        defines { "NDEBUG" }
        symbols "Off"
        optimize "On"

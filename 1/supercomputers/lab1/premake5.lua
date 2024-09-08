project "lab1"
    kind "ConsoleApp"
    language "C++"
    cppdialect "C++17"
    
    files { "**.hpp", "**.cpp" }

    buildoptions { "/openmp" }

    filter "configurations:Debug"
        defines { "DEBUG" }
        symbols "On"
        
    filter "configurations:Release"
        defines { "NDEBUG" }
        symbols "Off"
        optimize "On"

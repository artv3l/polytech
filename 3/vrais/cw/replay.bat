set PARAM=
if not "%~1"=="" set PARAM=-u%~1
spin652_windows64 -t -p %PARAM% -k test.pml.trail test.pml

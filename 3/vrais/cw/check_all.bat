spin652_windows64 -a test.pml
gcc -o pan.exe pan.c
for /L %%i in (1,1,%1) do (
    pan.exe -a -m100000 -N test%%i
)
del pan.*

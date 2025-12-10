spin652_windows64 -a model.pml
gcc -O2 -w -o pan.exe pan.c
for /L %%i in (1,1,%1) do (
    pan.exe -m100000000 -a -N test%%i
)
del pan.*

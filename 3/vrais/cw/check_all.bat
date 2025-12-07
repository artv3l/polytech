spin652_windows64 -a test.pml
gcc -DMEMLIM=1024 -O2 -DXUSAFE -DSAFETY -w -o pan.exe pan.c
for /L %%i in (1,1,%1) do (
    pan.exe -m100000 -N test%%i
)
del pan.*

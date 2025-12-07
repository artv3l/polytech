spin652_windows64 -a test.pml
gcc -DMEMLIM=1024 -O2 -DXUSAFE -DSAFETY -w -o pan.exe pan.c
pan.exe -m10000 -N %1
del pan.*

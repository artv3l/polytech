spin652_windows64 -a test.pml
gcc -o pan.exe pan.c
pan.exe -a -m100000 -N %1
del pan.*

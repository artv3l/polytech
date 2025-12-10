spin652_windows64 -a model.pml
gcc -O2 -w -o pan.exe pan.c
pan.exe -m100000000 -a -N %1
del pan.*

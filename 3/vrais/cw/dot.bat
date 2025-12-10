spin652_windows64 -a model.pml
gcc -O2 -w -o pan.exe pan.c
pan.exe -D > model.dot
del pan.*

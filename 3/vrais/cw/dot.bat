spin652_windows64 -a test.pml
gcc -o test.exe pan.c
test.exe -D > test.dot
del pan.*

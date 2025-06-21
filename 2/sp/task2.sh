#!/bin/bash

gcc -o kompassr.exe kompassr.c
./kompassr.exe task.ass
xxd -u -g 4 task.tex

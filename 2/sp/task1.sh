#!/bin/bash

gcc -o komppl.exe komppl.c
./komppl.exe task.pli
fold -w 80 task.ass

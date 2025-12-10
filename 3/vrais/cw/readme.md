# Install on Windows (with Chocolatey)

Установить Cygwin с пакетом gcc через инсталлер. Или с помощью cyg-get. Тогда нужно будет добавить в Path "C:\tools\cygwin\bin".

```
choco install cyg-get -y
cyg-get gcc-g++

choco install spin -y
choco install graphviz -y
choco install magicsplat-tcl-tk --version=1.11.2 -y
```

# GUI

Скачать файл: https://github.com/nimble-code/Spin/blob/master/optional_gui/ispin.tcl

Отредактировать, в разделе "Tools" указать путь к spin:

```
set SPIN    "C:/ProgramData/chocolatey/bin/spin652_windows64.exe"
```

Запуск GUI:

```
wish ispin.tcl
```

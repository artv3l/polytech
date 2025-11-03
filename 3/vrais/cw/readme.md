# Install on Windows (with Chocolatey)

Установить Cygwin с пакетом gcc. Через инсталлер или https://community.chocolatey.org/packages/cyg-get (не пробовал).

```
choco install spin -y
choco install magicsplat-tcl-tk --version=1.11.2 -y
choco install graphviz -y
```

Скачать файл https://github.com/nimble-code/Spin/blob/master/optional_gui/ispin.tcl

Отредактировать, в разделе "Tools" указать путь к spin:

```
set SPIN    "C:/ProgramData/chocolatey/bin/spin652_windows64.exe"
```

Запуск GUI:

```
wish ispin.tcl
```

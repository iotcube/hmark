# Hmark-4.0
Hmark for multilanguage(C/C+, Java, Python, Go, Javascript).
Hmark is a hash-index file generator. It is used to convert the C/C++ code into ".hidx" file. 
Hmark-4.0 is a new version of Hmark(https://github.com/Iotcube/hmark), which increases its functionality by making it possible to convert and scan source code of C/C++, Java, Python, Go and Javascript. Universal ctags(https://ctags.io/) is used as parsing tool.

### Usage

1. Download hmark for your OS from https://iotcube.net
2. Unzip the archive
3. Run the hmark

or 

1. Install python3
2. Choose the directory respective to your OS
3. 'python hmark.py [-h] [-c path ON/OFF] [-n] [-V]'

You can see the help message by passing an '-h' (or '--help')argument.
'''
- optional arguments:
    -h, --help               show the help message
    -c path ON/OFF, --cli-mode path ON/OFF
                             run Hmark in console mode by specifying the path 
                             to the target directory and the abstraction mode
    -n, --no-updatecheck     bypass update checking
    -V, --version            print the Hmark version
'''
4. Upload the '.hidx' file on IoTcube's (https://iotcube.net/process/type/wf1) testing.

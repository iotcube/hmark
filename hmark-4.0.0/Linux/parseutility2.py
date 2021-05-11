#!  /usr/bin/env python
"""
Parser utility.
Author: Seulbae Kim
Created: August 03, 2016
"""

import os
import sys
import subprocess
import re
import platform

def get_platform():
    global osName
    global bits

    pf = platform.platform()
    bits, _ = platform.architecture()
    if "Windows" in pf:
        osName = "win"
        bits = ""
    elif "Linux" in pf:
        osName = "linux"
        if "64" in bits:
            bits = "64"
        else:
            bits = "86"
    else:
        osName = "osx"
        bits = ""

class function:
    parentFile = None  # Absolute file which has the function
    parentNumLoc = None  # Number of LoC of the parent file
    name = None  # Name of the function
    lines = None  # Tuple (lineFrom, lineTo) that indicates the LoC of function
    funcId = None  # n, indicating n-th function in the file
    parameterList = []  # list of parameter variables
    variableList = []  # list of local variables
    dataTypeList = []  # list of data types, including user-defined types
    funcCalleeList = []  # list of called functions' names
    funcBody = None

    def __init__(self, fileName):
        self.parentFile = fileName
        self.parameterList = []
        self.variableList = []
        self.dataTypeList = []
        self.funcCalleeList = []

    def removeListDup(self):
        # for best performance, must execute this method
        # for every instance before applying the abstraction.
        self.parameterList = list(set(self.parameterList))
        self.variableList = list(set(self.variableList))
        self.dataTypeList = list(set(self.dataTypeList))
        self.funcCalleeList = list(set(self.funcCalleeList))

def loadSource(rootDirectory):
    # returns the list of .src files and its language under the specified root directory.
    maxFileSizeInBytes = None
    maxFileSizeInBytes = 2 * 1024 * 1024  # remove this line if you don't want to restrict
    # the maximum file size that you process.
    walkList = os.walk(rootDirectory)
    srcFileList = []
    for path, dirs, files in walkList:
        for fileName in files:
            ext = fileName.lower()
            if (ext.endswith('.c') or ext.endswith('.cpp')
            or ext.endswith('.cc') or ext.endswith('.c++')
            or ext.endswith('.cxx') or ext.endswith('.java')
            or ext.endswith('.py')) or ext.endswith('.go') or ext.endswith('.js'):
                absPathWithFileName = path.replace('\\', '/') + '/' + fileName
                if maxFileSizeInBytes is not None:
                    if os.path.getsize(absPathWithFileName) < maxFileSizeInBytes:
                        file = absPathWithFileName
                else:
                    file = absPathWithFileName
                if ext.endswith('.java'):
                    language = "java"
                elif ext.endswith('.py'):
                    language = "python"
                elif ext.endswith('.go'):
                    language = "go"
                elif ext.endswith('.js'):
                    language = "javascript"
                else:
                    language = "c"
                srcFileList.append((file, language))

    return srcFileList


def loadVul(rootDirectory):
    # returns the list of .vul files under the specified root directory.
    maxFileSizeInBytes = None
    # maxFileSizeInBytes = 2097152 # remove this line if you don't want to
    # restrict
    # the maximum file size that you process.
    walkList = os.walk(rootDirectory)
    srcFileList = []
    for path, dirs, files in walkList:
        for fileName in files:
            if fileName.endswith('OLD.vul'):
                absPathWithFileName = path.replace('\\', '/') + '/' + fileName
                if maxFileSizeInBytes is not None:
                    if os.path.getsize(absPathWithFileName) < maxFileSizeInBytes:
                        srcFileList.append(absPathWithFileName)
                else:
                    srcFileList.append(absPathWithFileName)
    return srcFileList


def removeComment(string, language):
    # Code for removing comments
    c_regex = re.compile(r'(?P<comment>//.*?$|[{}]+)|(?P<multilinecomment>/\*.*?\*/)|(?P<noncomment>\'(\\.|[^\\\'])*\'|"(\\.|[^\\"])*"|.[^/\'"]*)',
        re.DOTALL | re.MULTILINE)
    pythonShortComRegex = re.compile(r'(?!.*\"|.*\')[\r\t\f\v]*(#).*(?!.*\"|.*\')')
    pythonLongComRegex = re.compile(r"(\"\"\")(.|\n)*(\"\"\")")
    if language == "c" or language == "java" or language == "go" or language == "javascript" or language == "js":
        return ''.join([c.group('noncomment') for c in c_regex.finditer(string) if c.group('noncomment')])
    elif language == "python":
        string = pythonShortComRegex.sub("", string)
        return pythonLongComRegex.sub("", string)

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)


# def getBody(originalFunction):
#   # returns the function's body as a string.
#   return
#   originalFunction[originalFunction.find('{')+1:originalFunction.rfind('}')]
def normalize(string):
    # Code for normalizing the input string.
    # LF and TAB literals, curly braces, and spaces are removed,
    # and all characters are lowercased.
    return ''.join(string.replace('\n', '').replace('\r', '').replace('\t', '').replace('{', '').replace('}', '').split(' ')).lower()


def new_abstract(instance, level, language):
    # Applies abstraction on the function instance,
    # and then returns a tuple consisting of the original body and abstracted
    # body.
    originalFunctionBody = instance.funcBody
    originalFunctionBody = removeComment(originalFunctionBody, language)
    abstractBody = originalFunctionBody
    if language != "c":
        if int(level) >= 0:  # No abstraction.
            abstractBody = originalFunctionBody

        if int(level) >= 1:  # PARAM
            parameterList = instance.parameterList
            for param in parameterList:
                if len(param) == 0:
                    continue
                try:
                    paramPattern = re.compile("(?!.*\")(^|\(|\s)" + str(param)+ "(\W)(?!.*\")")
                    abstractBody = paramPattern.sub(r"\g<1>FPARAM\g<2>", abstractBody)
                except:
                    pass

        if int(level) >= 2:  # DTYPE
            dataTypeList = instance.dataTypeList
            for dtype in dataTypeList:
                if len(dtype) == 0:
                    continue
                try:
                    dtypePattern = re.compile("(?!.*\")(^|\(|\s)" + str(dtype)+ "(\W)(?!.*\")")
                    abstractBody = dtypePattern.sub(r"\g<1>DTYPE\g<2>", abstractBody)
                except:
                    pass

        if int(level) >= 3:  # LVAR
            variableList = instance.variableList
            for lvar in variableList:
                if len(lvar) == 0:
                    continue
                try:
                    lvarPattern = re.compile("(?!.*\")(^|\(|\s)" + str(lvar)+ "(\W)(?!.*\")")
                    abstractBody = lvarPattern.sub(r"\g<1>LVAR\g<2>", abstractBody)
                except:
                    pass
    else:
        if int(level) >= 0:  # No abstraction.
            abstractBody = originalFunctionBody

        if int(level) >= 1:  # PARAM
            parameterList = instance.parameterList
            for param in parameterList:
                if len(param) == 0:
                    continue
                try:
                    paramPattern = re.compile("(^|\W)" + param + "(\W)")
                    abstractBody = paramPattern.sub("\g<1>FPARAM\g<2>", abstractBody)
                except:
                    pass

        if int(level) >= 2:  # DTYPE
            dataTypeList = instance.dataTypeList
            for dtype in dataTypeList:
                if len(dtype) == 0:
                    continue
                try:
                    dtypePattern = re.compile("(^|\W)" + dtype + "(\W)")
                    abstractBody = dtypePattern.sub("\g<1>DTYPE\g<2>", abstractBody)
                except:
                    pass

        if int(level) >= 3:  # LVAR
            variableList = instance.variableList
            for lvar in variableList:
                if len(lvar) == 0:
                    continue
                try:
                    lvarPattern = re.compile("(^|\W)" + lvar + "(\W)")
                    abstractBody = lvarPattern.sub("\g<1>LVAR\g<2>", abstractBody)
                except:
                    pass
    return (originalFunctionBody, abstractBody)

delimiter = "\r\0?\r?\0\r"

#Shallow JAVA code parser using Universal-Ctags
def parse_java_shallow(file):
    pathToCtags = resource_path("ctags")
    Command = str(pathToCtags) + ' -f - --kinds-java=* --fields=neKS "' + file + '"'
    global delimiter
    delimiter = "\r\0?\r?\0\r"

    try:
        astString = subprocess.check_output(Command, stderr=subprocess.STDOUT, shell=True).decode(errors='ignore')

    except subprocess.CalledProcessError as e:
        print("Parser Error:", e)
        astString = ""

    f = open(file, 'r', encoding="utf8", errors='ignore')
    lines = f.readlines()
    methodList = astString.split('\n')
    method = re.compile(r'(method)')
    number = re.compile(r'(\d+)')
    funcBody = re.compile(r'{([\S\s]*)}')
    string = ""
    funcId = 1
    methodInstanceList = []

    for i in methodList:
        elemList = re.sub(r'[\t\s ]{2,}', '', i)
        elemList = elemList.split("\t")
        methodInstance = function(file)
        methodInstance.funcBody = ''
        if i != '' and len(elemList) >= 7 and method.match(elemList[3]):
            methodInstance.name = elemList[0]
            methodInstance.parentFile = elemList[1]
            methodInstance.lines = (int(number.search(elemList[4]).group(0)),
                                    int(number.search(elemList[6]).group(0)))
            methodInstance.parentNumLoc = len(lines)
            string = ""
            string = string.join(lines[methodInstance.lines[0]-1:methodInstance.lines[1]])
            if funcBody.search(string):
                methodInstance.funcBody = methodInstance.funcBody + funcBody.search(string).group(1)
            else:
                methodInstance.funcBody = " "
            methodInstance.funcId = funcId
            funcId+=1
            methodInstanceList.append(methodInstance)
    return methodInstanceList

#Deep JAVA code parser using Universal-Ctags
def parse_java_deep(file):
    pathToCtags = resource_path("ctags")
    Command = str(pathToCtags) + ' -f - --kinds-java=* --fields=neKS "' + file + '"'
    global delimiter
    delimiter = "\r\0?\r?\0\r"

    try:
        astString = subprocess.check_output(Command, stderr=subprocess.STDOUT, shell=True).decode(errors='ignore')

    except subprocess.CalledProcessError as e:
        print("Parser Error:", e)
        astString = ""

    f = open(file, 'r', encoding="utf8", errors='ignore')
    lines = f.readlines()
    methodList = astString.split('\n')
    local = re.compile(r'local')
    method = re.compile(r'(method)')
    parameterSpace = re.compile(r'\(\s*([^)]+?)\s*\)')
    word = re.compile(r'\w+')
#    dataType = re.compile()
    number = re.compile(r'(\d+)')
    funcBody = re.compile(r'{([\S\s]*)}')
    string = ""
    funcId = 1
    methodInstanceList = []
    variables = []
    for i in methodList:
        elemList = re.sub(r'[\t\s ]{2,}', '', i)
        elemList = elemList.split("\t")
        if i != '' and len(elemList) >= 6 and local.match(elemList[3]):
            variables.append(elemList)
    for i in methodList:
        elemList = re.sub(r'[\t\s ]{2,}', '', i)
        elemList = elemList.split("\t")
        methodInstance = function(file)
        methodInstance.funcBody = ''
        if i != ''  and len(elemList) >= 7 and method.match(elemList[3]):
            #Parameters and data types
            if (parameterSpace.search(elemList[5])):
                for i in parameterSpace.search(elemList[5])[1].split(", "):
                    if len(word.findall(i)) > 1:
                        methodInstance.parameterList.append(word.findall(i)[1])
                        methodInstance.dataTypeList.append(word.findall(i)[0])
            #Method body
            methodInstance.name = elemList[0]
            methodInstance.parentFile = elemList[1]
            methodInstance.lines = (int(number.search(elemList[4]).group(0)),
                                    int(number.search(elemList[6]).group(0)))
            methodInstance.parentNumLoc = len(lines)
            string = ""
            string = string.join(lines[methodInstance.lines[0]-1:methodInstance.lines[1]])
            if funcBody.search(string):
                methodInstance.funcBody = methodInstance.funcBody + funcBody.search(string).group(1)
            else:
                methodInstance.funcBody = " "
            #Variables
            for var in variables:
                if methodInstance.lines[0] <= int((number.search(var[4]).group(0))) <= methodInstance.lines[1]:
                    varDtype = re.compile(r'\w+(?=\s+' + str(var[0]) + ')')
                    if  varDtype.search(var[2]):
                        methodInstance.dataTypeList.append(varDtype.search(var[2]).group(0))
                        methodInstance.variableList.append(var[0])
            methodInstance.funcId = funcId
            funcId+=1
            methodInstanceList.append(methodInstance)
    return methodInstanceList

#Shallow PYTHON code parser using Universal-Ctags
def parse_python_shallow(file):
    pathToCtags = resource_path("ctags")
    Command = str(pathToCtags) + ' -f - --kinds-python=* --fields=neK "' + file + '"'
    global delimiter
    delimiter = "\r\0?\r?\0\r"

    try:
        astString = subprocess.check_output(Command, stderr=subprocess.STDOUT, shell=True).decode(errors='ignore')

    except subprocess.CalledProcessError as e:
        print("Parser Error:", e)
        astString = ""

    f = open(file, 'r', encoding="utf8", errors='ignore')
    lines = f.readlines()
    methodList = astString.split('\n')
    member = re.compile(r'(member)')
    func = re.compile(r'(function)')
    number = re.compile(r'(\d+)')
    methodInstanceList = []
    funcId = 1

    for i in methodList:
        elemList = re.sub(r'[\t\s ]{2,}', '', i)
        elemList = elemList.split("\t")
        methodInstance = function(file)
        methodInstance.funcBody = ''
        if i != '' and len(elemList) >= 6 and (member.match(elemList[3]) or func.match(elemList[3])):
            methodInstance.name = elemList[0]
            methodInstance.parentFile = elemList[1]
            methodInstance.funcId = funcId
            methodInstance.lines = (int(number.search(elemList[4]).group(0)),
                                    int(number.search(elemList[5]).group(0)))
            methodInstance.parentNumLoc = len(lines)
            for line in range(methodInstance.lines[0], methodInstance.lines[1]):
                methodInstance.funcBody = methodInstance.funcBody + (lines[line])
            funcId += 1
            methodInstanceList.append(methodInstance)

    return methodInstanceList

#Deep PYTHON code parser using Universal-Ctags
def parse_python_deep(file):
    pathToCtags = resource_path("ctags")
    Command = str(pathToCtags) + ' -f - --kinds-python=* --fields=neK "' + file + '"'
    global delimiter
    delimiter = "\r\0?\r?\0\r"
    try:
        astString = subprocess.check_output(Command, stderr=subprocess.STDOUT, shell=True).decode(errors='ignore')

    except subprocess.CalledProcessError as e:
        print("Parser Error:", e)
        astString = ""

    f = open(file, 'r', encoding="utf8", errors='ignore')
    lines = f.readlines()
    methodList = astString.split('\n')
    member = re.compile(r'(member)')
    func = re.compile(r'(function)')
    local = re.compile(r'(local)')
    parameter = re.compile(r'(parameter)')
    number = re.compile(r'\d+')
    methodInstanceList = []
    variables = []
    parameters = []
    funcId = 1
    #Variables list
    for i in methodList:
        elemList = re.sub(r'[\t\s ]{2,}', '', i)
        elemList = elemList.split("\t")
        if i != '' and local.match(elemList[3]):
            variables.append(elemList)

    #Parameters list
    for i in methodList:
        elemList = re.sub(r'[\t\s ]{2,}', '', i)
        elemList = elemList.split("\t")
        if i != '' and elemList[0] != 'self' and parameter.match(elemList[3]):
            parameters.append(elemList)

    #Function
    for i in methodList:
        elemList = re.sub(r'[\t\s ]{2,}', '', i)
        elemList = elemList.split("\t")
        methodInstance = function(file)
        methodInstance.funcBody = ''
        if i != '' and len(elemList) >= 6 and (member.match(elemList[3]) or func.match(elemList[3])):
            methodInstance.name = elemList[0]
            methodInstance.parentFile = elemList[1]
            methodInstance.lines = (int(number.search(elemList[4]).group(0)),
                                    int(number.search(elemList[5]).group(0)))
            methodInstance.parentNumLoc = len(lines)
            for line in range(methodInstance.lines[0], methodInstance.lines[1]):
                methodInstance.funcBody = methodInstance.funcBody + (lines[line])
            methodInstance.funcId = funcId
            funcId += 1
            #Variables
            for var in variables:
                if methodInstance.lines[0] <= int(number.search(var[4]).group(0)) <= methodInstance.lines[1]:
                    methodInstance.variableList.append(var[0])
                    #Parameters
            for param in parameters:
                if methodInstance.lines[0] <= int(number.search(param[4]).group(0)) <= methodInstance.lines[1]:
                    methodInstance.parameterList.append(param[0])
            methodInstanceList.append(methodInstance)

    return methodInstanceList

#Shallow GO code parser using Universal-Ctags
def parse_go_shallow(file):
    pathToCtags = resource_path("ctags")
    Command = str(pathToCtags) + ' -f - --kinds-go=* --fields=neKSt "' + file + '"'
    global delimiter
    delimiter = "\r\0?\r?\0\r"
    functionInstanceList = []

    try:
        astString = subprocess.check_output(Command, stderr=subprocess.STDOUT, shell=True).decode(errors='ignore')

    except subprocess.CalledProcessError as e:
        print("Parser Error:", e)
        astString = ""

    f = open(file, 'r', encoding="utf8", errors='ignore')
    lines = f.readlines()
    functionList = astString.split('\n')
    func = re.compile(r'(func)')
    number = re.compile(r'(\d+)')
    funcBody = re.compile(r'{([\S\s]*)}')

    string = " "
    firstLine = 0
    funcId = 1

    for i in functionList:
        elemList = re.sub(r'[\t\s ]{2,}', '', i)
        elemList = elemList.split("\t")
        functionInstance = function(file)
        functionInstance.funcBody = ''
        if i != '' and len(elemList) >= 8 and func.fullmatch(elemList[3])  and re.match(r"(end:)(\d+)", elemList[7]):
            functionInstance.name = elemList[0]
            functionInstance.parentFile = elemList[1]
            functionInstance.parentNumLoc = len(lines)
            if number.search(elemList[4]):
                firstLine = int(number.search(elemList[4]).group(0))
            elif number.search(elemList[5]):
                firstLine = int(number.search(elemList[5]).group(0))
            else:
                continue
            functionInstance.lines = (firstLine,
                                      int(number.search(elemList[7]).group(0)))
            string = " "

            if len(lines)-1 >= functionInstance.lines[0]:
                if func.search(lines[functionInstance.lines[0]]):
                    string = string.join(lines[functionInstance.lines[0]:functionInstance.lines[1]])
            if func.search(lines[functionInstance.lines[0]-1]):
                string = string.join(lines[functionInstance.lines[0]-1:functionInstance.lines[1]])
            elif func.search(lines[functionInstance.lines[0]-2]):
                string = string.join(lines[functionInstance.lines[0]-2:functionInstance.lines[1]])

            if funcBody.search(string):
                functionInstance.funcBody = functionInstance.funcBody + funcBody.search(string).group(1)
            else:
                functionInstance.funcBody = " "
            functionInstance.funcId = funcId
            funcId += 1
            functionInstanceList.append(functionInstance)
    return functionInstanceList

#Deep GO code parser using Universal-Ctags
def parse_go_deep(file):
    pathToCtags = resource_path("ctags")
    Command = str(pathToCtags) + ' -f - --kinds-go=* --fields=neKSt "' + file + '"'
    global delimiter
    delimiter = "\r\0?\r?\0\r"
    functionInstanceList = []

    try:
        astString = subprocess.check_output(Command, stderr=subprocess.STDOUT, shell=True).decode(errors='ignore')

    except subprocess.CalledProcessError as e:
        print("Parser Error:", e)
        astString = ""

    f = open(file, 'r', encoding="utf8", errors='ignore')
    lines = f.readlines()
    functionList = astString.split('\n')
    varRe = re.compile(r'(var)')
    dataType = re.compile(r'')
    func = re.compile(r'(func)')
    number = re.compile(r'(\d+)')
    funcBody = re.compile(r'{([\S\s]*)}')

    string = " "
    firstLine = 0
    funcId = 1

    for i in functionList:
        elemList = re.sub(r'[\t\s ]{2,}', '', i)
        elemList = elemList.split("\t")
        functionInstance = function(file)
        functionInstance.funcBody = ''
        if i != ''  and len(elemList) >= 8 and (func.fullmatch(elemList[3]) or func.fullmatch(elemList[4]))  and re.match(r"(end:)(\d+)", elemList[7]):
            functionInstance.name = elemList[0]
            functionInstance.parentFile = elemList[1]
            functionInstance.parentNumLoc = len(lines)
            if number.search(elemList[4]):
                firstLine = int(number.search(elemList[4]).group(0))
            elif number.search(elemList[5]):
                firstLine = int(number.search(elemList[5]).group(0))
            else:
                continue

            functionInstance.lines = (firstLine,
                                      int(number.search(elemList[7]).group(0)))
            string = " "

            if len(lines)-1 >= functionInstance.lines[0]:
                if func.search(lines[functionInstance.lines[0]]):
                    string = string.join(lines[functionInstance.lines[0]:functionInstance.lines[1]])
            if func.search(lines[functionInstance.lines[0]-1]):
                string = string.join(lines[functionInstance.lines[0]-1:functionInstance.lines[1]])
            elif func.search(lines[functionInstance.lines[0]-2]):
                string = string.join(lines[functionInstance.lines[0]-2:functionInstance.lines[1]])

            if funcBody.search(string):
                functionInstance.funcBody = functionInstance.funcBody + funcBody.search(string).group(1)
            else:
                functionInstance.funcBody = " "
            functionInstance.funcId = funcId
            funcId += 1
            #Data types
            elemList[5] = re.sub("(typeref:typename:)", "", elemList[5])
            if re.search(r'\(\s*([^)]+?)\s*\)', elemList[5]):
                for dType in re.search(r'\(\s*([^)]+?)\s*\)', elemList[5]).group(1).split(", "):
                    functionInstance.dataTypeList.append(re.search("\S+$", dType).group(0))
                    dType = re.sub("\S+$", "", dType)
                    if dType:
                        functionInstance.variableList.append(re.search("\S+", dType).group(0))
            elif re.match(r'^\S+$', elemList[5]):
                functionInstance.dataTypeList.append(re.match(r'^\S+$', elemList[5]).group(0))

            parameter = re.compile(r"^(\S+)")
            parameterSpace = []
            #Parameters
            elemList[6] = re.sub("(signature:)", "", elemList[6])
            if re.search(r'\(\s*([^)]+?)\s*\)', elemList[6]):
                parameterSpace = re.search(r'\(\s*([^)]+?)\s*\)', elemList[6]).group(1).split(", ")
                for elem in parameterSpace:
                    elem = re.sub("(,)", "", elem)
                    functionInstance.parameterList.append(parameter.search(elem).group(0))
                    elem = re.sub(parameter, "", elem)
                    if re.search("\S+", elem):
                        functionInstance.dataTypeList.append(re.search("\S+", elem).group(0))

            #Variables
            filee = open("function.go", "w+", encoding="utf8", errors='ignore')
            filee.write(functionInstance.funcBody)
            filee.close()
            Command1 = str(pathToCtags) + ' -f - --kinds-go=* --fields=neKS "function.go"'
            shellOutput = subprocess.check_output(Command1, stderr=subprocess.STDOUT, shell=True).decode()
            varList = []
            varList = shellOutput.split('\n')
            for var in varList:
                elemsList = re.sub(r'[\t\s ]{2,}', '', var)
                elemsList = elemsList.split("\t")
                if var != '' and (varRe.match(elemsList[3]) or varRe.match(elemsList[4])):
                    functionInstance.variableList.append(elemsList[0])
            functionInstanceList.append(functionInstance)

    return functionInstanceList

#Shallow JavaScript code parser using Universal-Ctags
def parse_js_shallow(file):
    pathToCtags = resource_path("ctags")
    Command = str(pathToCtags) + ' -f - --kinds-javascript=* --fields=neKS "' + file + '"'
    global delimiter
    delimiter = "\r\0?\r?\0\r"
    functionInstanceList = []

    try:
        astString = subprocess.check_output(Command, stderr=subprocess.STDOUT, shell=True).decode(errors='ignore')
    except subprocess.CalledProcessError as e:
        print("Parser Error:", e)
        astString = ""

    f = open(file, 'r', encoding="utf8", errors='ignore')
    lines = f.readlines()
    functionList = astString.split('\n')
    func = re.compile(r'(function)')
    method = re.compile(r'(method)')
    number = re.compile(r'(\d+)')
    new_line = re.compile(r'(\n)')

    string = " "
    funcId = 1
    lines_count = 0

    for i in functionList:
        elemList = re.sub(r'[\t\s ]{2,}', '', i)
        elemList = elemList.split("\t")
        functionInstance = function(file)
        functionInstance.funcBody = ''
        if i != '' and len(elemList) >= 6 and (func.fullmatch(elemList[3]) or method.fullmatch(elemList[3])):
            functionInstance.name = elemList[0]
            functionInstance.parentFile = elemList[1]
            functionInstance.parentNumLoc = len(lines)
            string = " "
            string = string.join(lines[int(number.search(elemList[4]).group(0))-1:])
            funcString = ""
            ctr = 0
            flag = 0
            for c in string:
                if c == "{":
                    ctr = ctr + 1
                    flag = 1
                elif c == "}":
                    ctr = ctr - 1
                if ctr == 0 and flag == 1:
                    break
                elif ctr != 0 and flag == 1 and c != "{" and c != "}":
                    funcString = funcString + c

            functionInstance.funcBody = functionInstance.funcBody + funcString
            functionInstance.lines = (int(number.search(elemList[4]).group(0)),
                                      int(number.search(elemList[4]).group(0)) + functionInstance.funcBody.count("\n"))
            functionInstance.funcId = funcId
            funcId += 1
            functionInstanceList.append(functionInstance)

    return functionInstanceList

#Shallow JavaScript code parser using Universal-Ctags
def parse_js_deep(file):
    pathToCtags = resource_path("ctags")
    Command = str(pathToCtags) + ' -f - --kinds-javascript=* --fields=neKS "' + file + '"'
    global delimiter
    delimiter = "\r\0?\r?\0\r"
    functionInstanceList = []

    try:
        astString = subprocess.check_output(Command, stderr=subprocess.STDOUT, shell=True).decode(errors='ignore')

    except subprocess.CalledProcessError as e:
        print("Parser Error:", e)
        astString = ""

    f = open(file, 'r', encoding="utf8", errors='ignore')
    lines = f.readlines()
    functionList = astString.split('\n')
    func = re.compile(r'(function)')
    varRe = re.compile(r'(var)')
    parameter = re.compile(r'\(\s*([^)]+?)\s*\)')
    variableRe = re.compile(r'(variable)')
    method = re.compile(r'(method)')
    number = re.compile(r'(\d+)')
    new_line = re.compile(r'(\n)')

    string = " "
    funcId = 1
    lines_count = 0
    for i in functionList:
        elemList = re.sub(r'[\t\s ]{2,}', '', i)
        elemList = elemList.split("\t")
        functionInstance = function(file)
        functionInstance.funcBody = ''
        if i != '' and len(elemList) >= 6 and (func.fullmatch(elemList[3]) or method.fullmatch(elemList[3])):
            functionInstance.name = elemList[0]
            functionInstance.parentFile = elemList[1]
            functionInstance.parentNumLoc = len(lines)
            string = " "
            string = string.join(lines[int(number.search(elemList[4]).group(0))-1:])
            funcString = ""
            ctr = 0
            flag = 0
            for c in string:
                if c == "{":
                    ctr = ctr + 1
                    flag = 1
                elif c == "}":
                    ctr = ctr - 1
                if ctr == 0 and flag == 1:
                    break
                elif ctr != 0 and flag == 1 and c != "{" and c != "}":
                    funcString = funcString + c

            functionInstance.funcBody = functionInstance.funcBody + funcString
            functionInstance.lines = (int(number.search(elemList[4]).group(0)),
                                      int(number.search(elemList[4]).group(0)) + functionInstance.funcBody.count("\n"))
            functionInstance.funcId = funcId
            funcId += 1

            #Parameters
            if parameter.search(elemList[5]):
                functionInstance.parameterList.append(parameter.search(elemList[5]).group(1))

            #Variables
            filee = open("function.js", "w+", encoding="utf8", errors='ignore')
            filee.write(functionInstance.funcBody)
            filee.close()
            Command1 = str(pathToCtags) + ' -f - --kinds-javascript=* --fields=neKS function.js'
            shellOutput = subprocess.check_output(Command1, stderr=subprocess.STDOUT, shell=True).decode()
            varList = []
            varList = shellOutput.split('\n')
            for var in varList:
                elemsList = re.sub(r'[\t\s ]{2,}', '', var)
                elemsList = elemsList.split("\t")
                if var != '' and len(elemsList) >= 4 and ((varRe.fullmatch(elemsList[3]) or variableRe.fullmatch(elemsList[3]))):
                    functionInstance.variableList.append(elemsList[0])

            functionInstanceList.append(functionInstance)
    return functionInstanceList


def parse_c_shallow(file):
    pathToCtags = resource_path("ctags")
    Command = str(pathToCtags) + ' -f - --kinds-C=* --fields=neKSt "' + file + '"'
    global delimiter
    delimiter = "\r\0?\r?\0\r"

    try:
        astString = subprocess.check_output(Command, stderr=subprocess.STDOUT, shell=True).decode(errors='ignore')

    except subprocess.CalledProcessError as e:
        print("Parser Error:", e)
        astString = ""

    f = open(file, 'r', encoding="utf8", errors='ignore')
    lines = f.readlines()
    functionList = astString.split('\n')
    func = re.compile(r'(function)')
    number = re.compile(r'(\d+)')
    funcBody = re.compile(r'{([\S\s]*)}')
    string = ""
    funcId = 1
    functionInstanceList = []

    for i in functionList:
        elemList = re.sub(r'[\t\s ]{2,}', '', i)
        elemList = elemList.split("\t")
        functionInstance = function(file)
        functionInstance.funcBody = ''
        if i != '' and len(elemList) >= 8 and func.fullmatch(elemList[3]):
            functionInstance.name = elemList[0]
            functionInstance.parentFile = elemList[1]
            functionInstance.lines = (int(number.search(elemList[4]).group(0)),
                                    int(number.search(elemList[7]).group(0)))
            functionInstance.parentNumLoc = len(lines)
            string = ""
            string = string.join(lines[functionInstance.lines[0]-1:functionInstance.lines[1]])
            if funcBody.search(string):
                functionInstance.funcBody = functionInstance.funcBody + funcBody.search(string).group(1)
            else:
                functionInstance.funcBody = " "
            functionInstance.funcId = funcId
            funcId+=1
            functionInstanceList.append(functionInstance)
    return functionInstanceList

def parse_c_deep(file):
    pathToCtags = resource_path("ctags")
    Command = str(pathToCtags) + ' -f - --kinds-C=* --fields=neKSt "' + file + '"'
    global delimiter
    delimiter = "\r\0?\r?\0\r"

    try:
        astString = subprocess.check_output(Command, stderr=subprocess.STDOUT, shell=True).decode(errors='ignore')

    except subprocess.CalledProcessError as e:
        print("Parser Error:", e)
        astString = ""

    f = open(file, 'r', encoding="utf8", errors='ignore')
    lines = f.readlines()
    functionList = astString.split('\n')
    local = re.compile(r'local')
    parameter = re.compile(r'parameter')
    func = re.compile(r'(function)')
    parameterSpace = re.compile(r'\(\s*([^)]+?)\s*\)')
    word = re.compile(r'\w+')
    dataType = re.compile(r"(typeref:)\w*(:)")
    number = re.compile(r'(\d+)')
    funcBody = re.compile(r'{([\S\s]*)}')
    string = ""
    funcId = 1
    functionInstanceList = []
    variables = []
    parameters = []
    dataTypes = []
    for i in functionList:
        elemList = re.sub(r'[\t\s ]{2,}', '', i)
        elemList = elemList.split("\t")
        if i != '' and len(elemList) >= 6 and (local.fullmatch(elemList[3]) or local.fullmatch(elemList[4])):
            variables.append(elemList)

    for i in functionList:
        elemList = re.sub(r'[\t\s ]{2,}', '', i)
        elemList = elemList.split("\t")
        if i != '' and len(elemList) >= 6 and (parameter.match(elemList[3]) or parameter.fullmatch(elemList[4])):
            parameters.append(elemList)

    for i in functionList:
        elemList = re.sub(r'[\t\s ]{2,}', '', i)
        elemList = elemList.split("\t")
        functionInstance = function(file)
        functionInstance.funcBody = ''
        if i != ''  and len(elemList) >= 8 and func.fullmatch(elemList[3]):
            #Method body
            functionInstance.name = elemList[0]
            functionInstance.parentFile = elemList[1]
            functionInstance.lines = (int(number.search(elemList[4]).group(0)),
                                    int(number.search(elemList[7]).group(0)))
            functionInstance.parentNumLoc = len(lines)
            string = ""
            string = string.join(lines[functionInstance.lines[0]-1:functionInstance.lines[1]])
            if funcBody.search(string):
                functionInstance.funcBody = functionInstance.funcBody + funcBody.search(string).group(1)
            else:
                functionInstance.funcBody = " "
            lineNumber = 0
            #Parameters
            for param in parameters:
                if number.search(param[4]):
                    lineNumber = int(number.search(param[4]).group(0))
                elif number.search(param[5]):
                    lineNumber = int(number.search(param[5]).group(0))
                if len(param) >= 4 and functionInstance.lines[0] <= int(lineNumber) <= functionInstance.lines[1]:
                    functionInstance.parameterList.append(param[0])
                    if len(param) >= 6 and dataType.search(param[5]):
                        functionInstance.dataTypeList.append(re.sub(r" \*$", "", dataType.sub("", param[5])))
                    elif len(param) >= 7 and dataType.search(param[6]):
                        functionInstance.dataTypeList.append(re.sub(r" \*$", "", dataType.sub("", param[6])))
            #Variables
            for variable in variables:
                if number.search(variable[4]):
                    lineNumber = int(number.search(variable[4]).group(0))
                elif number.search(variable[5]):
                    lineNumber = int(number.search(variable[5]).group(0))
                if len(variable) >= 4 and functionInstance.lines[0] <= int(lineNumber) <= functionInstance.lines[1]:
                    functionInstance.variableList.append(variable[0])
                    if len(variable) >= 6 and dataType.search(variable[5]):
                        functionInstance.dataTypeList.append(re.sub(r" \*$", "", dataType.sub("", variable[5])))
                    elif len(variable) >= 7 and dataType.search(variable[6]):
                        functionInstance.dataTypeList.append(re.sub(r" \*$", "", dataType.sub("", variable[6])))                        

            functionInstance.funcId = funcId
            funcId+=1
            functionInstanceList.append(functionInstance)
    return functionInstanceList

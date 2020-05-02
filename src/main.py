import codeparser
import lexer
import codegen
import json
import sys

cfgFilePath = "config.json"
cfg = json.loads(open(cfgFilePath).read())

inputFile = cfg["inputFile"]
outputFile = cfg["outputFile"]
run = cfg["run"]
codegen.useTypeHints = cfg["useTypeHints"]
includeHeader = cfg["includeHeader"]
lexer.passPseudocodeAsComment = cfg["passPseudocodeAsComment"]
lexer.passThroughComments = cfg["passThroughComments"]

if run:
    # There is no point in using type hints when running only
    codegen.useTypeHints = False 
    # Header must be included to run
    includeHeader = True

f = open(inputFile, encoding="UTF-8").read()

tokens = lexer.lex(f)

parseTree = codeparser.parse(tokens)

res = codegen.codegen(parseTree)

header = ""

if codegen.shouldIncludeRandom:
    header = header + "import random\n"
if codegen.shouldIncludeDataclass:
    header = header + "from dataclasses import dataclass\n"
if codegen.shouldIncludeFiles:
    files = open("src/std/files.py").read()
    header = header + files

if includeHeader:
    res = header + res

if run:
    exec(res)
elif outputFile is not None:
    g = open(outputFile, "w")
    print(res, g)
    g.close()
else:
    print(res)
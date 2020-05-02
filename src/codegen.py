def codegen(program):
    output = ""
    for statement in program:
        output += genTree(statement) + "\n"
    return output

builtIns = {"LENGTH", "LEFT", "RIGHT", "RND", "RANDOMBETWEEN"}
builtInTypes = {"STRING": "str", "INTEGER": "int", "BOOLEAN": "bool", "BOOL": "bool", "CHAR": "str"}
typesNoInit = {"str", "int", "bool", "float"}

useTypeHints = False
shouldIncludeFiles = False
shouldIncludeRandom = False
shouldIncludeDataclass = False

def genBuiltInFn(fnName, params):
    global shouldIncludeRandom
    if fnName == "LENGTH":
        return f"len({genTree(params)})"
    if fnName == "LEFT":
        varName, length = f"{genTree(params)}".split(", ")
        return f"{varName}[:{length}]"
    if fnName == "RIGHT":
        varName, length = f"{genTree(params)}".split(", ")
        return f"{varName}[-({length}):]"
    if fnName == "RND":
        shouldIncludeRandom = True
        return f"random.random()"
    if fnName == "RANDOMBETWEEN":
        shouldIncludeRandom = True
        a, b = f"{genTree(params)}".split(", ")
        return f"random.randint({a}, {b})"

uid = 0
fNameDict : dict = {}

def fileVarName(filename):
    global uid
    if filename not in fNameDict.keys():
        uid += 1
        fNameDict[filename] = uid
    return f"file{fNameDict[filename]}"

def genTree(tree):
    global shouldIncludeFiles, shouldIncludeDataclass
    if tree is None:
        return ""
    treeTy = tree[0]
    if treeTy == "COMMENT":
        return f"# {tree[1]}"
    elif treeTy == "ASSIGN":
        return f"{genTree(tree[1])} = {genTree(tree[2])}"
    elif treeTy == "OUTPUT":
        return f"print({genTree(tree[1])})"
    elif treeTy == "VARIABLE":
        return tree[1]
    elif treeTy == "INDEX":
        # Pseudocode is 1-based, Python is 0-based
        return f"{genTree(tree[1])}[{genTree(tree[2])} - 1]"
    elif treeTy == "FIELD":
        return f"{genTree(tree[1])}.{genTree(tree[2])}"
    elif treeTy == "STRING":
        return f"\"{tree[1]}\""
    elif treeTy == "ADD":
        return f"({genTree(tree[1])} + {genTree(tree[2])})"
    elif treeTy == "SUB":
        return f"({genTree(tree[1])} - {genTree(tree[2])})"
    elif treeTy == "NEG":
        return f"(-{genTree(tree[1])})"
    elif treeTy == "MUL":
        return f"({genTree(tree[1])} * {genTree(tree[2])})"
    elif treeTy == "DIV":
        return f"({genTree(tree[1])} / {genTree(tree[2])})"
    elif treeTy == "INTEGER" or treeTy == "FLOAT":
        return f"{tree[1]}"
    elif treeTy == "COMMA":
        return f"{genTree(tree[1])}, {genTree(tree[2])}"
    elif treeTy == "BOOLEAN":
        if tree[1] == "TRUE":
            return "True"
        else:
            return "False"
    elif treeTy == "OR":
        return f"{genTree(tree[1])} or {genTree(tree[2])}"
    elif treeTy == "EQ":
        return f"{genTree(tree[1])} == {genTree(tree[2])}"
    elif treeTy == "GT":
        return f"{genTree(tree[1])} > {genTree(tree[2])}"
    elif treeTy == "LT":
        return f"{genTree(tree[1])} < {genTree(tree[2])}"
    elif treeTy == "REPEAT":
        cond, block = tree[1], tree[2]
        genBlock = "\n".join(map(lambda s: "    " + s, codegen(block).splitlines()))
        return f"while True:\n{genBlock}\n    if {genTree(cond)}:\n        break"
    elif treeTy == "WHILE":
        cond, block = tree[1], tree[2]
        genBlock = "\n".join(map(lambda s: "    " + s, codegen(block).splitlines()))
        return f"while {genTree(cond)}:\n{genBlock}"
    elif treeTy == "FOR":
        _, counter, values, block = tree
        genBlock = "\n".join(map(lambda s: "    " + s, codegen(block).splitlines()))
        return f"for {genTree(counter)} in {genTree(values)}:\n{genBlock}"
    elif treeTy == "TO":
        _, start, end = tree
        return f"range({genTree(start)}, {genTree(end)} + 1)"
    elif treeTy == "IF":
        _, cond, b1, b2 = tree
        genB1 = "\n".join(map(lambda s: "    " + s, codegen(b1).splitlines()))
        tmp = f"if {genTree(cond)}:\n{genB1}"
        if b2 is not None:
            genB2 = "\n".join(map(lambda s: "    " + s, codegen(b2).splitlines()))
            tmp += f"\nelse:\n{genB2}"
        return tmp
    elif treeTy == "FUNCTION":
        _, fnName, params, block = tree
        genBlock = "\n".join(map(lambda s: "    " + s, codegen(block).splitlines()))
        if params[0] == "RETURNS":
            genParams, returnTy = genTree(params[1]), genTree(params[2])
            if useTypeHints:
                return f"def {genTree(fnName)}({genParams}) -> {returnTy}:\n{genBlock}"
            else:
                return f"def {genTree(fnName)}({genParams}):\n{genBlock}"
        else:
            genParams = genTree(params)
            return f"def {genTree(fnName)}({genParams}):\n{genBlock}"
    elif treeTy == "CALL":
        _, fnName, params = tree
        if fnName in builtIns:
            return genBuiltInFn(fnName, params)
        genParams = genTree(params)
        return f"{fnName}({genParams})"
    elif treeTy == "RETURN":
        return f"return {genTree(tree[1])}"
    elif treeTy == "OPENFILE":
        _, fName, mode = tree
        fName = genTree(fName)
        varName = fileVarName(fName)
        shouldIncludeFiles = True
        return f"{varName} = FileHandler({fName}, '{mode}')"
    elif treeTy == "READFILE":
        _, fName, varName = tree[1]
        return f"{genTree(varName)} = {fileVarName(genTree(fName))}.readLine()"
    elif treeTy == "WRITEFILE":
        _, fName, expr = tree[1]
        return f"{fileVarName(genTree(fName))}.writeLine({genTree(expr)})"
    elif treeTy == "CLOSEFILE":
        return f"{fileVarName(genTree(tree[1]))}.closeFile()"
    elif treeTy == "COLON":
        _, varName, varTy = tree
        if useTypeHints:
            return f"{genTree(varName)}: {genTree(varTy)}"
        return genTree(varName)
    elif treeTy == "KEYWORD":
        _, kw = tree
        if kw in builtInTypes.keys():
            return builtInTypes[kw]
    elif treeTy == "ARRAY":
        _, vals = tree
        return f"[{genTree(vals)}]"
    elif treeTy == "DECLARE":
        _, lhs, rhs = tree
        ty = genTree(rhs)
        if ty in typesNoInit:
            return f"{genTree(lhs)} : {ty}"
        else:
            if rhs[0] == "OF":
                _, arTy, ty = rhs
                listLen = arTy[1][2]
                ty = genTree(ty)
                if ty in typesNoInit:
                    return f"{genTree(lhs)} : list = [None for _ in range({genTree(listLen)})]"
                else:
                    return f"{genTree(lhs)} : list = [{ty}() for _ in range({genTree(listLen)})]"
            else:
                return f"{genTree(lhs)} : {ty} = {ty}()"
    elif treeTy == "TYPE":
        _, TName, TBody = tree
        shouldIncludeDataclass = True
        genBlock = "\n".join(map(lambda s: "    " + s + " = None", codegen(TBody).splitlines()))
        return f"@dataclass\nclass {genTree(TName)}:\n{genBlock}"
    elif treeTy == "OF":
        # List tree, it's possible to use Python's typing library to be more
        # precise about the type, but right now it is not necessary
        return "list"
    else:
        print("Unknown Tree:", tree)
        return ""
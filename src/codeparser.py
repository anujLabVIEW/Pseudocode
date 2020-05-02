def isA(token, tt=None, tv=None):
    """
    function to check if a token meets certain criteria
    """
    # Row and column info may be useful? for error messages
    try:
        tokTT, tokTV, _row, _col = token
    except:
        return False
    if tt is None and tv is None:
        return True
    elif tv is None:
        return tt == tokTT
    elif tt is None:
        return tv == tokTV
    else:
        return tv == tokTV and tt == tokTT

def keyword(token, kw=None):
    """
    function to check if a token is a (certain) keyword
    """
    return isA(token, tt="KEYWORD", tv=kw)

def symbol(token, sym=None):
    """
    function to check if a token is a (certain) symbol
    """
    return isA(token, tt="SYMBOL", tv=sym)

def identifier(token, ident=None):
    """
    function to check if a token is a (certain) identifier
    """
    return isA(token, tt="IDENTIFIER", tv=ident)

def replace(tree, placeholder, value):
    if tree == placeholder:
        tree.clear()
        for v in value:
            tree.append(v)
    else:
        for i in range(len(tree)):
            if tree[i] == placeholder:
                tree[i] = value
            elif type(tree[i]) is list:
                replace(tree[i], placeholder, value)

uid = 0
def getUID():
    global uid
    uid += 1
    # Max placeholder depth
    uid %= 10000
    return uid

def parseExpression(tokens):
    """
    Function to parse expressions
    """
    # If the length is 1 then it is atomic, ie the token is the expression
    if len(tokens) == 1:
        tt, tv, *_ = tokens[0]
        if tt == "FLOAT" or tt == "INTEGER" or tt == "STRING" or tt == "BOOLEAN":
            return [tt, tv]
        elif tt == "IDENTIFIER":
            return ["VARIABLE", tv]
        elif tt == "PLACEHOLDER":
            return ["PLACEHOLDER", tv]
        elif tt == "KEYWORD":
            return ["KEYWORD", tv]
    if len(tokens) == 0:
        return

    if symbol(tokens[0], "-"):
        return ["NEG", parseExpression(tokens[1:])]
    if keyword(tokens[0], "NOT"):
        return ["NOT", parseExpression(tokens[1:])]

    # Check for field access:
    dotIdx = next((i for i, e in enumerate(tokens) if symbol(e, ".")), -1)
    if dotIdx != -1:
        lvalue = parseExpression(tokens[:dotIdx])
        rvalue = parseExpression(tokens[dotIdx + 1:])
        return ["FIELD", lvalue, rvalue]

    oob = len(tokens) + 1

    # Check for brackets
    lbrIdx = next((i for i, e in enumerate(tokens) if symbol(e, "(")), oob)
    if lbrIdx != oob:
        brDepth = 0
        # Find the matching right bracket
        for i in range(lbrIdx, len(tokens)):
            tok = tokens[i]
            if symbol(tok, "("):
                brDepth += 1
            elif symbol(tok, ")"):
                brDepth -= 1
                if brDepth == 0:
                    rbrIdx = i
                    break
        # Parse the expression inside the brackets
        inner = tokens[lbrIdx + 1:rbrIdx]
        innerRes = parseExpression(inner)
        placeHolderID = getUID()
        placeHolder = ("PLACEHOLDER", placeHolderID, -1, -1)
        # If the token preceding a identifier then it is a function call
        if identifier(tokens[lbrIdx - 1]):
            expr = tokens[:lbrIdx - 1] + [placeHolder] + tokens[rbrIdx + 1:]
            exprParsed = parseExpression(expr)
            _, fnName, *_ = tokens[lbrIdx - 1]
            replace(exprParsed, ["PLACEHOLDER", placeHolderID], ["CALL", fnName, innerRes])
        # Otherwise, it is a parenthesised expression
        else:
            expr = tokens[:lbrIdx] + [placeHolder] + tokens[rbrIdx + 1:]
            exprParsed = parseExpression(expr)
            replace(exprParsed, ["PLACEHOLDER", placeHolderID], innerRes)
        return exprParsed

    # Check for square brackets
    lbrIdx = next((i for i, e in enumerate(tokens) if symbol(e, "[")), oob)
    if lbrIdx != oob:
        brDepth = 0
        # Find the matching right bracket
        for i in range(lbrIdx, len(tokens)):
            tok = tokens[i]
            if symbol(tok, "["):
                brDepth += 1
            elif symbol(tok, "]"):
                brDepth -= 1
                if brDepth == 0:
                    rbrIdx = i
                    break
        # Parse the expression inside the brackets
        inner = tokens[lbrIdx + 1:rbrIdx]
        innerRes = parseExpression(inner)
        placeHolderID = getUID()
        placeHolder = ("PLACEHOLDER", placeHolderID, -1, -1)
        # If the token preceding a identifier then it is an indexing op
        if identifier(tokens[lbrIdx - 1]):
            expr = tokens[:lbrIdx - 1] + [placeHolder] + tokens[rbrIdx + 1:]
            exprParsed = parseExpression(expr)
            _, varName, *_ = tokens[lbrIdx - 1]
            replace(exprParsed, ["PLACEHOLDER", placeHolderID], ["INDEX", ["VARIABLE", varName], innerRes])
        # Otherwise, it is an array
        else:
            expr = tokens[:lbrIdx] + [placeHolder] + tokens[rbrIdx + 1:]
            exprParsed = parseExpression(expr)
            replace(exprParsed, ["PLACEHOLDER", placeHolderID], ["ARRAY", innerRes])
        return exprParsed
    
    symbParseOrder = [
        (",", "COMMA"),
        (":", "COLON"),
        (">", "GT"),
        ("<", "LT"),
        ("<=", "LE"),
        (">=", "GE"),
        ("<>", "NE"),
        ("=", "EQ"),
        ("+", "ADD"),
        ("-", "SUB"),
        ("*", "MUL"),
        ("/", "DIV")
    ]

    # Try parse for infix symbols
    for symb, op in symbParseOrder:
        idx = next((i for i, e in enumerate(tokens) if symbol(e, symb)), oob)
        if idx != oob:
            lvalue = parseExpression(tokens[:idx])
            rvalue = parseExpression(tokens[idx + 1:])
            return [op, lvalue, rvalue]

    kwParseOrder = [
        ("MOD", "MOD"),
        ("DIV", "FLDIV"),
        ("AND", "AND"),
        ("OR", "OR"),
        ("RETURNS", "RETURNS"),
        ("OF", "OF"), 
        ("TO", "TO")
    ]

    for kw, op in kwParseOrder:
        idx = next((i for i, e in enumerate(tokens) if keyword(e, kw)), oob)
        if idx != oob:
            lvalue = parseExpression(tokens[:idx])
            rvalue = parseExpression(tokens[idx + 1:])
            return [op, lvalue, rvalue]
    
    if keyword(tokens[0], "CALL") or keyword(tokens[0], "ARRAY"):
        return parseExpression(tokens[1:])
        

def parseAssignment(tokens):
    opIndex = next(i for i, e in enumerate(tokens) if symbol(e, "<-"))
    lvalue = parseExpression(tokens[:opIndex])
    rvalue = parseExpression(tokens[opIndex+1:])
    return ["ASSIGN", lvalue, rvalue]

def findKwLine(tokens, kw, start=0):
    depth = 0
    incrToken, decrToken = kw, "END" + kw
    if kw == "UNTIL":
        incrToken, decrToken = "REPEAT", "UNTIL"
    if kw == "ELSE":
        incrToken, decrToken = "IF", "ELSE"
    for i in range(start + 1, len(tokens)):
        if keyword(tokens[i][0], incrToken):
            depth += 1
        elif keyword(tokens[i][0], decrToken):
            if depth > 0:
                depth -= 1
            else:
                return i
    return -1

def parse(tokens):
    tree = []
    lineNum = 0
    l = len(tokens)
    while lineNum < l:
        # print(lineNum)
        line = tokens[lineNum]
        if line[0][0] == "COMMENT":
            tree.append(["COMMENT", line[0][1]])
        elif keyword(line[0], "DECLARE"):
            opIndex = next(i for i, e in enumerate(line) if symbol(e, ":"))
            lvalue = parseExpression(line[1:opIndex])
            rvalue = parseExpression(line[opIndex+1:])
            tree.append(["DECLARE", lvalue, rvalue])
        elif keyword(line[0], "FOR"):
            endl = findKwLine(tokens, "FOR", lineNum)
            opIndex = next(i for i, e in enumerate(line) if symbol(e, "<-"))
            counter = parseExpression(line[1:opIndex])
            body = parse(tokens[lineNum + 1:endl])
            rhs = parseExpression(line[opIndex + 1:])
            lineNum = endl
            tree.append(["FOR", counter, rhs, body])
        elif any(map(lambda s: symbol(s, "<-"), line)):
            tree.append(parseAssignment(line))
        elif keyword(line[0], "FUNCTION"):
            endl = findKwLine(tokens, "FUNCTION", lineNum)
            body = parse(tokens[lineNum + 1:endl])
            fnName = parseExpression([line[1]])
            header = parseExpression(line[2:])
            lineNum = endl
            tree.append(["FUNCTION", fnName, header, body])
        elif keyword(line[0], "TYPE"):
            endl = findKwLine(tokens, "TYPE", lineNum)
            body = parse(tokens[lineNum + 1:endl])
            tyName = parseExpression([line[1]])
            lineNum = endl
            tree.append(["TYPE", tyName, body])
        elif keyword(line[0], "PROCEDURE"):
            endl = findKwLine(tokens, "PROCEDURE", lineNum)
            body = parse(tokens[lineNum + 1:endl])
            fnName = parseExpression([line[1]])
            header = parseExpression(line[2:])
            lineNum = endl
            tree.append(["FUNCTION", fnName, header, body])
        elif keyword(line[0], "IF"):
            elsel = findKwLine(tokens, "ELSE", lineNum)
            endl = findKwLine(tokens, "IF", lineNum)
            header = parseExpression(line[1:])
            if elsel == -1:
                body = parse(tokens[lineNum + 1:endl])
                tree.append(["IF", header, body, None])
            else:
                b1 = parse(tokens[lineNum + 1:elsel])
                b2 = parse(tokens[elsel+1:endl])
                tree.append(["IF", header, b1, b2])
            lineNum = endl
        elif keyword(line[0], "REPEAT"):
            endl = findKwLine(tokens, "UNTIL", lineNum)
            cond = parseExpression(tokens[endl][1:])
            body = parse(tokens[lineNum + 1:endl])
            tree.append(["REPEAT", cond, body])
            lineNum = endl
        elif keyword(line[0], "WHILE"):
            endl = findKwLine(tokens, "WHILE", lineNum)
            cond = parseExpression(line[1:])
            body = parse(tokens[lineNum + 1:endl])
            tree.append(["WHILE", cond, body])
            lineNum = endl
        elif keyword(line[0], "OUTPUT"):
            tree.append(["OUTPUT", parseExpression(line[1:])])
        elif keyword(line[0], "RETURN"):
            tree.append(["RETURN", parseExpression(line[1:])])
        elif keyword(line[0], "OPENFILE"):
            fname = parseExpression([line[1]])
            mode = line[3][1][0].lower()
            if mode not in "rwa":
                print(f"Unknown File Mode: {line[3][1]}")
            tree.append(["OPENFILE", fname, mode])
        elif keyword(line[0], "READFILE"):
            tree.append(["READFILE", parseExpression(line[1:])])
        elif keyword(line[0], "WRITEFILE"):
            tree.append(["WRITEFILE", parseExpression(line[1:])])
        elif keyword(line[0], "CLOSEFILE"):
            tree.append(["CLOSEFILE", parseExpression(line[1:])])
        else:
            try:
                lineAsExp = parseExpression(line)
                if lineAsExp is not None:
                    tree.append(lineAsExp)
                else:
                    print("Unknown Line", line)
            except:
                print("Unknown Line", line)
        lineNum += 1
    return tree
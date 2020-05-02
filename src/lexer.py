keywords = {
            "FUNCTION", "ENDFUNCTION", "PROCEDURE", "ENDPROCEDURE",
            "ARRAY", "OF", 
            "INTEGER", "BOOL", "FLOAT", "STRING", "BOOLEAN", "CHAR",
            "FOR", "ENDFOR", "TO",
            "WHILE", "ENDWHILE",
            "REPEAT", "UNTIL",
            "IF", "THEN", "ENDIF", "ELSE",
            "OUTPUT", "INPUT",
            "DECLARE",
            "AND", "OR", "NOT",
            "MOD", "DIV",
            "RETURN", "RETURNS",

            "OPENFILE", "CLOSEFILE", "READ", "WRITE", "APPEND",
            "READFILE", "WRITEFILE",
            "CALL",

            "TYPE", "ENDTYPE"
            }
symbols = {":", ",", "(", ")", "<-", 
           "=", "<>", ">", "<", "<=", ">=", 
           "+", "-", "*", "/",
           "[", "]", "."}

def classifyToken(s: str, row: int, startCol: int):
    """
    Classifying the tokens produced by the lexer. There are sets above which
    contains the values for the keywords and symbols, so anything that comes up
    there is classfied as such.

    Then integers are classfied, then it is checked if it is an identifier.
    Finally it checks if the number is a float.

    If all checks fails, then the token is UNCLASSIFIED. The program does not
    panic here.

    Row and Col here are zero indexed.
    """
    tokType = "UNCLASSIFIED"
    if s in keywords:
        tokType = "KEYWORD"
    elif s == "TRUE" or s == "FALSE":
        tokType = "BOOLEAN"
    elif s in symbols:
        tokType = "SYMBOL"
    elif s.isnumeric():
        tokType = "INTEGER"
    elif s.isalnum():
        # if s.upper() == s:
        #     print(f"Potential Keyword? : {s}")
        tokType = "IDENTIFIER"
    else:
        try:
            float(s)
            tokType = "FLOAT"
        except: pass
    return (tokType, s, row, startCol)

passThroughComments = False
passPseudocodeAsComment = False

def classifyChar(c: str):
    """
    A function that classifies characters into groups, used for separating one
    token from another

    Even though, alpha ("a") and digits ("d") can be used exchangably
    for some scenarios (identifiers), there are scenarios where this is not the
    case, which is why there are two groups.

    a.a is field access syntax, whereas d.d is a float. a.d and d.a are invalid syntax.
    """
    if c.isalpha():
        return "a"
    elif c.isdigit():
        return "d"
    else:
        return "u"

def noChars(s):
    return not any(map(lambda x: x.isalpha(), s))

def lex(s: str):
    """
    Function to turn input string into list of tokens

    The algorithm to determine when a token ends and the next one begins
    (for tokens that are not space separated) is to look at the type of
    the previous and current characters. If they match, then they are part
    of the same token. If they are different, then the current token has
    ended and the next one begins.

    However this doesn't lex floats, so the previous token is stored as a
    special case handler for floating point numbers.
    """
    # List of tokens
    tokens = []
    lines = s.splitlines()
    for row in range(len(lines)):
        l = lines[row]
        # Ignore indentation
        content = l.lstrip()
        # Ignore blank lines
        if content == "" or content == "THEN":
            continue
        if content.startswith("//"):
            if passThroughComments:
                tokens.append([("COMMENT", content[2:].lstrip(), row, -1)])
            continue
        if passPseudocodeAsComment:
            tokens.append([("COMMENT", content, row, -1)])
        offset = len(l) - len(content)
        # Current Tokens in this line
        lineToks = []
        # Current Token
        currTok = ""
        # Initialise the type of the previous character to the type of the first character
        prevCharTy = classifyChar(content[0])
        prevChar = ""
        tokStartCol = 0

        isString = False
        currStr = ""

        for col in range(len(content)):
            char = content[col]
            if char == "\"":
                if not isString:
                    lineToks.append(classifyToken(currTok, row, tokStartCol + offset))
                    tokStartCol = col
                    currTok = ""
                else:
                    lineToks.append(("STRING", currStr, row, tokStartCol + offset))
                    currStr = ""
                isString = not isString
                continue
            if isString:
                currStr += char
                continue

            # Whitespace is the end of the current token
            if char == " ":
                # Dump token, which ignores consecutive whitespace
                if currTok != "":
                    lineToks.append(classifyToken(currTok, row, tokStartCol + offset))
                    currTok = ""
                prevChar = " "
                continue

            currCharTy = classifyChar(char)
            # If the previous char is whitespace, then the classification in currCharTy doesn't matter
            if prevChar == " ":
                currTok += char
                tokStartCol = col
                prevCharTy = currCharTy
                prevChar = char
                continue

            # If the type matches, then continue the current token
            if currCharTy == prevCharTy:
                currTok += char

            # Special Case for Floats
            elif prevCharTy == "d" and char == "." and noChars(currTok):
                currTok += char
            elif prevChar == "." and currCharTy == "d" and noChars(currTok):
                currTok += char

            # Special case for alnum identifiers:
            elif currTok.isalnum() and (currCharTy == "d" or currCharTy == "a"):
                currTok += char

            # If the type don't match, then the current token has ended
            elif currCharTy != prevCharTy:
                lineToks.append(classifyToken(currTok, row, tokStartCol + offset))
                tokStartCol = col
                currTok = char

            # Update variables for next iteration of the loop
            prevCharTy = currCharTy
            prevChar = char
        # Add on the remaining tokens
        lineToks.append(classifyToken(currTok, row, tokStartCol + offset))
        tokens.append(lineToks)
    # For each unclassified token, try splitting it into individual characters and lexing again
    newToks = []
    for line in tokens:
        newline = []
        for token in line:
            tt, tv, row, col = token
            if tt != "UNCLASSIFIED":
                newline.append(token)
            else:
                separate = [classifyToken(e, row, col+i) for i,e in enumerate(tv)]
                newline += separate
        newToks.append(newline)
    return newToks
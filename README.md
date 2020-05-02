# CIE CompSci Pseudocode Lexer/Parser/Compiler

Lexer takes code, and generates a list of tokens `(TokenType, TokenValue, Row, Col)` for each line. `Row` may not match the row of the array as the lexer ignores blank lines.

Parser generates a parse tree. First item is the type, rest are the items.

Codegen transforms that into Python code.

## Looking at this Repo

* `src/main.py` is the main progam. You want to run it from the root folder of the repo (the folder this README is in).
* `config.json` is the temporary way which is used to tell main program what to do. The input file is specified there. There are a number of flags:
  * `run` - whether to `exec` the output, or print the generated Python file.
  * `outputFile` - where to save the generated file
  * `useTypeHints` - should type hints be added to the output file, so that tools like `mypy` can process it
  * `includeHeader` - whether to include all of the definitions required. The way that I implemented the file reading API is with a thin wrapper above the Python API
  * `passPseudocodeAsComment` - Whether the pseudocode should be added in as a comment into the Python output
  * `passThroughComments` - Should comments from the Pseudocode be copied over to the Python code
* `src/lexer.py` is the lexer
* `src/codeparser.py` is the parser
* `src/codegen.py` is the codegen backend (right now it outputs to Python. I don't think it'd be too difficult to add a new backend, although I'd need to add an API for that).
* `src/std/files.py` is the files wrapper so that the behaviour matches the pseudocode
* `examples` is a bunch of example files which I used to test the program.

## Suggestions/PR/etc

Suggestions and PR are welcome, but since it's been so long since I wrote this, I'm not too sure about how the implementation works.

This code is licensed under Apache-2.0.

## Issues To be handled

* Codegen doesn't handle all cases at the moment, just handled as they come up
* `CASE` Statement. `OF` appears in two locations, and the grammar would be more complex. I don't think any lookahead is necessary, but I'm not sure.
* Records in Files
* BIDMAS - Parser knows BIDMAS, but codegen doesn't. So there's going to be a lot more brackets than necessary.

## Potential Features

* Directives? Are they needed? or is it better to have it as a config file instead

## Longer Term / Maybe Never

* Complex Indexing, so `a[b][c]` or `a.b[c]`. This would probably require a rewrite of the parser, so it may not ever happen
* Error messages. At the moment they are REALLY bad (just Python crashes). Not sure entirely how this could be improved though
* Using Python's `typing` library for Array and other types

## Probably Never handling

* `BYREF` and `BYVAL`. It's probably possible to do so by defining a custom reference type, or using Python's copy, but it's too much effort. The parser side isn't too bad as it is just adding a prefix operator for the expression parser. The main issue here is tha Python's default behaviour is not consistent, as with some types it is by value (`int`, `float` etc.) but for others (`list`) it is by reference. If all types were by reference, then it would be possible to just use `copy` when a parameter is passed by value. Perhaps wrapping the Python `copy` types in a custom class can fix this issue? But then it would need to be done for all types and variables, and probably isn't worth the hassle.

## Error Message Hints

`TypeError` in `treeTy = tree[0]` is probably either an unknown keyword or an unhandled case in the parser. Right now there is a catch for `None` in `codegen.genTree`, but it might cause issues.

`ValueError: too many values to unpack` is probable when a value is passed when an array should have been passed through, ie when `T` is passed instead of `[T]`.

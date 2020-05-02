class FileHandler():
    def __init__(self, filename, mode):
        self.f = open(filename, mode)
        if mode == "r": self.data = self.f.read().splitlines()
    def readLine(self): return self.data.pop(0)
    def eol(self): return len(self.data) == 0
    def writeLine(self, line): print(line, file=self.f)
    def closeFile(self): self.f.close()


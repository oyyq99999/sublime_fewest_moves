from .move_transformer import tokenize, parse_move
class FaceletCube:

    def __init__(self, scramble = ''):
        # URFDLB
        # 012345
        # B face viewed with y2
        self.state = [
            [0, 0, 0, 0, 0, 0, 0, 0, 0],
            [1, 1, 1, 1, 1, 1, 1, 1, 1],
            [2, 2, 2, 2, 2, 2, 2, 2, 2],
            [3, 3, 3, 3, 3, 3, 3, 3, 3],
            [4, 4, 4, 4, 4, 4, 4, 4, 4],
            [5, 5, 5, 5, 5, 5, 5, 5, 5],
        ]
        self.apply(scramble)

    def apply(self, scramble):
        moves = tokenize(scramble)
        for move in moves:
            axis, amount = parse_move(move)
            self.makeMove(axis, amount)

    def makeMove(self, axis, amount):
        for i in range(amount):
            if axis == 0:
                self.moveU()
                continue
            if axis == 1:
                self.moveR()
                continue
            if axis == 2:
                self.moveF()
                continue
            if axis == 3:
                self.moveD()
                continue
            if axis == 4:
                self.moveL()
                continue
            if axis == 5:
                self.moveB()
                continue

    def moveU(self):
        self.swap(0, 0, 0, 2, 0, 8, 0, 6)
        self.swap(0, 1, 0, 5, 0, 7, 0, 3)
        self.swap(1, 0, 2, 0, 4, 0, 5, 0)
        self.swap(1, 1, 2, 1, 4, 1, 5, 1)
        self.swap(1, 2, 2, 2, 4, 2, 5, 2)
    def moveR(self):
        self.swap(1, 0, 1, 2, 1, 8, 1, 6)
        self.swap(1, 1, 1, 5, 1, 7, 1, 3)
        self.swap(0, 2, 5, 6, 3, 2, 2, 2)
        self.swap(0, 5, 5, 3, 3, 5, 2, 5)
        self.swap(0, 8, 5, 0, 3, 8, 2, 8)
    def moveF(self):
        self.swap(2, 0, 2, 2, 2, 8, 2, 6)
        self.swap(2, 1, 2, 5, 2, 7, 2, 3)
        self.swap(0, 6, 1, 0, 3, 2, 4, 8)
        self.swap(0, 7, 1, 3, 3, 1, 4, 5)
        self.swap(0, 8, 1, 6, 3, 0, 4, 2)
    def moveD(self):
        self.swap(3, 0, 3, 2, 3, 8, 3, 6)
        self.swap(3, 1, 3, 5, 3, 7, 3, 3)
        self.swap(1, 6, 5, 6, 4, 6, 2, 6)
        self.swap(1, 7, 5, 7, 4, 7, 2, 7)
        self.swap(1, 8, 5, 8, 4, 8, 2, 8)
    def moveL(self):
        self.swap(4, 0, 4, 2, 4, 8, 4, 6)
        self.swap(4, 1, 4, 5, 4, 7, 4, 3)
        self.swap(0, 0, 2, 0, 3, 0, 5, 8)
        self.swap(0, 3, 2, 3, 3, 3, 5, 5)
        self.swap(0, 6, 2, 6, 3, 6, 5, 2)
    def moveB(self):
        self.swap(5, 0, 5, 2, 5, 8, 5, 6)
        self.swap(5, 1, 5, 5, 5, 7, 5, 3)
        self.swap(0, 0, 4, 6, 3, 8, 1, 2)
        self.swap(0, 1, 4, 3, 3, 7, 1, 5)
        self.swap(0, 2, 4, 0, 3, 6, 1, 8)

    def swap(self, a, b, c, d, e, f, g, h):
        tmp = self.state[a][b]
        self.state[a][b] = self.state[g][h]
        self.state[g][h] = self.state[e][f]
        self.state[e][f] = self.state[c][d]
        self.state[c][d] = tmp


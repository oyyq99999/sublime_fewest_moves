import re

AXES = 'URFDLB'
ROTATIONS = ['y', 'x', 'z']

# orientations:
# UF UR UB UL FD FR FU FL DB DR DF DL BU BR BD BL RF RD RB RU LF LU LB LD
#  0  1  2  3  4  5  6  7  8  9 10 11 12 13 14 15 16 17 18 19 20 21 22 23
def reorient(current, axis, amount):
    MAPPING = [
        [1, 4, 20],
        [2, 17, 5],
        [3, 14, 18],
        [0, 23, 15],
        [5, 8, 23],
        [6, 18, 9],
        [7, 2, 19],
        [4, 22, 3],
        [9, 12, 22],
        [10, 19, 13],
        [11, 6, 16],
        [8, 21, 7],
        [13, 0, 21],
        [14, 16, 1],
        [15, 10, 17],
        [12, 20, 11],
        [17, 7, 0],
        [18, 11, 4],
        [19, 15, 8],
        [16, 3, 12],
        [21, 5, 10],
        [22, 1, 6],
        [23, 13, 2],
        [20, 9, 14],
    ]
    next = current
    for i in range(amount):
        next = MAPPING[next][axis]
    return next

def oriented_move(move, orientation):
    MAPPING = {
        'U': [
            'U', 'U', 'U', 'U',
            'F', 'F', 'F', 'F',
            'D', 'D', 'D', 'D',
            'B', 'B', 'B', 'B',
            'R', 'R', 'R', 'R',
            'L', 'L', 'L', 'L',
        ],
        'R': [
            'R', 'B', 'L', 'F',
            'R', 'U', 'L', 'D',
            'R', 'F', 'L', 'B',
            'R', 'D', 'L', 'U',
            'D', 'B', 'U', 'F',
            'U', 'B', 'D', 'F',
        ],
        'F': [
            'F', 'R', 'B', 'L',
            'D', 'R', 'U', 'L',
            'B', 'R', 'F', 'L',
            'U', 'R', 'D', 'L',
            'F', 'D', 'B', 'U',
            'F', 'U', 'B', 'D',
        ],
    }
    axis = AXES.index(move[:1])
    suffix = move[1:]
    opposite = False
    if axis >= 3:
        opposite = True
        axis %= 3
    newFace = MAPPING[AXES[axis]][orientation]
    if opposite:
        newAxis = (AXES.index(newFace) + 3) % 6
        newFace = AXES[newAxis]
    return newFace + suffix

def tokenize(sequence):
    move_pattern = re.compile(r"((?:2?[URFDLB]w|[URFDLBxyz])['2]?|\[[urfdlb]['2]?\]|[Nn][Ii][Ss][Ss])")
    return move_pattern.findall(sequence)

def parse_move(move):
    axis = AXES.index(move[:1])
    amount = suffix2amount(move[1:])
    return (axis, amount)

def compose_move(axis, amount):
    move = AXES[axis]
    if amount == 2:
        move += '2'
    if amount == 3:
        move += "'"
    return move

def suffix2amount(suffix):
    suffix = '0' if not suffix else suffix
    return "02'".index(suffix) + 1

def amount2suffix(amount):
    suffixes = [None, '', '2', "'"]
    return suffixes[amount % 4]

def reverse_suffix(suffix):
    return ["'", '2', ''][suffix2amount(suffix) - 1]

def equivalence_mapping(move, suffix):
    axis = move[0:1]
    amount = suffix2amount(suffix)
    result = []

    idx = -1
    if axis in AXES:
        idx = AXES.index(axis)
        newMove = AXES[(idx + 3) % 6] + suffix
        result.append(newMove)
    else:
        idx = AXES.index(axis.upper())

    reverse = False
    if idx >= 3:
        idx %= 3
        reverse = True
    rotation = ROTATIONS[idx] + (reverse_suffix(suffix) if reverse else suffix)
    result.append(rotation)
    return result

def standardize(sequence):
    irregular_move_pattern = re.compile(r"^(?:2?([URFDLB]w)(['2]?)|\[([urfdlb])(['2]?)\])$")
    result = []
    for move in sequence:
        match = irregular_move_pattern.search(move)
        if match is not None:
            if match.group(1) is not None:
                equivalent = equivalence_mapping(match.group(1), match.group(2))
                result += equivalent
            else:
                equivalent = equivalence_mapping(match.group(3), match.group(4))
                result += equivalent
        else:
            result.append(move)
    return result

def regularize(sequence):
    tmp = standardize(sequence)

    result = []
    orientation = 0
    for move in tmp:
        axis = move[:1]
        amount = suffix2amount(move[1:])
        if axis in ROTATIONS:
            orientation = reorient(orientation, ROTATIONS.index(axis), amount)
            continue
        result.append(oriented_move(move, orientation))
    return result

def normalize(sequence):
    tokens = tokenize(sequence)
    normal_sequence = []
    inverse_sequence = []
    inverse = False
    for token in tokens:
        if token.upper() == 'NISS':
            inverse = not inverse
            continue
        if inverse:
            inverse_sequence.append(token)
        else:
            normal_sequence.append(token)
    reverse = standardize(inverse_sequence[::-1])
    for move in reverse:
        if move.endswith("'"):
            normal_sequence.append(move[:-1])
        elif move.endswith("2"):
            normal_sequence.append(move)
        else:
            normal_sequence.append(move + "'")
    normal_sequence = regularize(normal_sequence)
    result = []
    for move in normal_sequence:
        axis, amount = parse_move(move)
        if len(result) > 0:
            lastAxis, lastAmount = parse_move(result[-1])
            if axis == lastAxis:
                amount += lastAmount
                amount %= 4
                if amount == 0:
                    del result[-1]
                else:
                    result[-1] = compose_move(axis, amount)
                continue
            elif len(result) > 1 and axis % 3 == lastAxis % 3:
                previousAxis, previousAmount = parse_move(result[-2])
                if axis == previousAxis:
                    amount += previousAmount
                    amount %= 4
                    if amount == 0:
                        del result[-2]
                    else:
                        result[-2] = compose_move(axis, amount)
                    continue
        result.append(move)
    return ' '.join(result)

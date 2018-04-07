import re

AXES = 'URFDLB'

def tokenize(sequence):
    # move_pattern = re.compile(r"((?:[URFDLBxyz]|\[[urfdlb]\]|2?[URFDLB]w)['2]?|[Nn][Ii][Ss][Ss])")
    move_pattern = re.compile(r"([URFDLB]['2]?|[Nn][Ii][Ss][Ss])")
    return move_pattern.findall(sequence)

def parse_move(move):
    axis = AXES.index(move[:1])
    suffix = move[1:]
    suffix = '0' if not suffix else suffix
    amount = "02'".index(suffix) + 1
    return (axis, amount)

def compose_move(axis, amount):
    move = AXES[axis]
    if amount == 2:
        move += '2'
    if amount == 3:
        move += "'"
    return move

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
    reverse = inverse_sequence[::-1]
    for move in reverse:
        if move.endswith("'"):
            normal_sequence.append(move[:-1])
        elif move.endswith("2"):
            normal_sequence.append(move)
        else:
            normal_sequence.append(move + "'")
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
    return ' '.join(normal_sequence)


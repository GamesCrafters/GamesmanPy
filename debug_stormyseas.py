import sys
sys.path[:0] = ['games/src', 'models/src', 'interfaces/src', 'server/src', 'solver/src']
from games.stormyseassmall import StormySeas

g = StormySeas('a')
print('row_length', g.row_length, 'num_rows', g.num_rows)

s = 'owbwwwoowBwrwooowwRwwowowwwoowwwowo'
rows = [s[i:i+g.row_length] for i in range(0, g.num_rows * g.row_length, g.row_length)]
print('rows', rows)

binary_str = ''
boat_positions = {}
for row_idx, row in enumerate(rows):
    for col_idx, char in enumerate(row):
        if char == 'w':
            binary_str += '1'
        elif char == 'o':
            binary_str += '0'
        elif char.upper() in g.colors:
            binary_str += '0'
            if char.isupper():
                boat_positions[char.upper()] = (row_idx, col_idx)
        else:
            binary_str += '0'

print('binary_str', binary_str)
print('boat_positions', boat_positions)

boat_pos_list = []
for color in g.colors:
    if color in boat_positions:
        row, col = boat_positions[color]
        boat_pos_list.append(f'{row}{col}')
print('boat_pos_list', boat_pos_list)

full_string = binary_str + ''.join(boat_pos_list)
print('full_string', full_string)
print('len full_string', len(full_string))
print('untranslate output', g.untranslate(full_string))
print('hash input', g.untranslate(full_string))
print('hash result', g.hash(g.untranslate(full_string)))

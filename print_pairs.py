

raw = """GRAPH_ID VEHICLE_ID
3 6
11 2
82 1
7 5
58 3
32 2
50 1
2 6
21 0
67 0
17 0
54 0
81 0
6 11
40 0
71 0
57 3
36 0
13 2
30 0
9 6
66 0
1 4
10 6
70 0
16 0
79 1
73 1
53 0
49 3
63 1
35 0"""

# 5 11 - took 10 hrs


pairs = []
for line in raw.split('\n')[1:]:
    numbers = line.split(' ')
    numbers = [int(n) for n in numbers]
    pairs.append(numbers)

greedy_alg = ['s', 'd5', 'dinf', 'f']

for pair in pairs:
    for g in greedy_alg:
        print(f"{g} {pair[0]} {pair[1]}")
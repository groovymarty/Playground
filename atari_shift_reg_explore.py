from collections import deque

MODES = ("gnd", "center", "5v")

def next_state(state, mode):
    b6 = (state >> 6) & 1
    b5 = (state >> 5) & 1

    if mode == "gnd":
        other = 0
    elif mode == "5v":
        other = 1
    else:
        other = b5

    feedback = b6 ^ other
    return ((state & 0x7F) << 1) | feedback

start = 0xFF
seen = {start}
queue = deque([start])

while queue:
    state = queue.popleft()

    for mode in MODES:
        new_state = next_state(state, mode)

        if new_state not in seen:
            seen.add(new_state)
            queue.append(new_state)

print(len(seen))
print(sorted(set(range(256)) - seen))

cycles = []
for mode in MODES:
    cycle_seen = set()
    for start_state in range(0, 256):
        state = start_state
        seen = set()
        # look for a cycle
        while state not in seen:
            seen.add(state)
            state = next_state(state, mode)
        # found cycle
        if state not in cycle_seen:
            sequence = []
            while state not in cycle_seen:
                cycle_seen.add(state)
                sequence.append(state)
                state = next_state(state, mode)
            cycle = (mode, sequence)
            cycles.append(cycle)

for cycle in cycles:
    mode, sequence = cycle
    seq_hex = " ".join([f"{state:02x}" for state in sequence])
    print(f"mode {mode}: len {len(sequence)}: {seq_hex}")

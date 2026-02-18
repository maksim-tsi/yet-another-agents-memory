from datasets.locations import LocationsDataset


def apply_move(current_location: list[int], move: tuple[int, int]) -> None:
    current_location[0] += move[0]
    current_location[1] += move[1]


def parse_out_directions(statements: list[str]) -> list[tuple[int, int]]:
    moves = []

    for stmt in statements:
        # Get the distance
        for w in stmt.split(" "):
            if w.isnumeric():
                dist = int(w)
                break

        if "North" in stmt:
            moves.append((0, dist))
        elif "South" in stmt:
            moves.append((0, -dist))
        elif "East" in stmt:
            moves.append((dist, 0))
        elif "West" in stmt:
            moves.append((-dist, 0))

    return moves


def test_location_generation() -> None:
    dataset = LocationsDataset()
    data = dataset.generate_examples(100)
    for d in data:
        moves = parse_out_directions(d.script)

        current_location = [0, 0]
        for m in moves:
            apply_move(current_location, m)

        assert current_location[0] == 0 or current_location[1] == 0

        if "same location" not in d.expected_responses:
            last_move = parse_out_directions([f"{d.expected_responses}"])[0]
            apply_move(current_location, last_move)

        assert current_location[0] == 0 and current_location[1] == 0

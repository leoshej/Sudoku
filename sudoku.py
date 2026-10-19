"""Sudoku generator and solver."""

import random


def is_valid(board, row, col, value):
    if value in board[row]:
        return False

    for r in range(9):
        if board[r][col] == value:
            return False

    box_row, box_col = 3 * (row // 3), 3 * (col // 3)
    for r in range(box_row, box_row + 3):
        for c in range(box_col, box_col + 3):
            if board[r][c] == value:
                return False

    return True


def count_solutions(board):
    empty_cell = None
    for r in range(9):
        for c in range(9):
            if board[r][c] == 0:
                empty_cell = (r, c)
                break
        if empty_cell:
            break

    if not empty_cell:
        return 1

    row, col = empty_cell
    count = 0
    for value in range(1, 10):
        if is_valid(board, row, col, value):
            board[row][col] = value
            count += count_solutions(board)
            board[row][col] = 0
            if count > 1:
                return 2

    return count


def fill_board(board):
    empty_cell = None
    for r in range(9):
        for c in range(9):
            if board[r][c] == 0:
                empty_cell = (r, c)
                break
        if empty_cell:
            break

    if not empty_cell:
        return True

    row, col = empty_cell
    numbers = list(range(1, 10))
    random.shuffle(numbers)

    for value in numbers:
        if is_valid(board, row, col, value):
            board[row][col] = value
            if fill_board(board):
                return True
            board[row][col] = 0

    return False


def remove_numbers(board, cells_to_remove):
    coords = [(r, c) for r in range(9) for c in range(9)]
    random.shuffle(coords)

    removed = 0
    for row, col in coords:
        if removed >= cells_to_remove:
            break

        original_value = board[row][col]
        board[row][col] = 0

        board_copy = [line[:] for line in board]
        if count_solutions(board_copy) != 1:
            board[row][col] = original_value
        else:
            removed += 1

    return board


def is_solved(grid):
    if not grid or len(grid) != 9 or not all(isinstance(row, list) and len(row) == 9 for row in grid):
        return False

    valid_set = set(range(1, 10))
    for i in range(9):
        if set(grid[i]) != valid_set:
            return False
        column = [grid[r][i] for r in range(9)]
        if set(column) != valid_set:
            return False

    for i in range(0, 9, 3):
        for j in range(0, 9, 3):
            block = [grid[r][c] for r in range(i, i + 3) for c in range(j, j + 3)]
            if set(block) != valid_set:
                return False

    return True


def determine_complexity(input_grid):
    board = [row[:] for row in input_grid]
    score = 0
    candidates = [[set() for _ in range(9)] for _ in range(9)]
    candidates_active = False

    def all_groups():
        groups = []
        for i in range(9):
            groups.append([(i, c) for c in range(9)])
        for i in range(9):
            groups.append([(r, i) for r in range(9)])
        for block_index in range(9):
            start_row, start_col = (block_index // 3) * 3, (block_index % 3) * 3
            groups.append([(r, c) for r in range(start_row, start_row + 3) for c in range(start_col, start_col + 3)])
        return groups

    def refresh_candidates():
        for r in range(9):
            for c in range(9):
                if board[r][c] == 0:
                    valid_numbers = set()
                    for value in range(1, 10):
                        if is_valid(board, r, c, value):
                            valid_numbers.add(value)
                    candidates[r][c] = valid_numbers
                else:
                    candidates[r][c] = set()

    def update_after_move(row, col, value):
        if not candidates_active:
            return
        for i in range(9):
            candidates[row][i].discard(value)
        for i in range(9):
            candidates[i][col].discard(value)
        start_row, start_col = (row // 3) * 3, (col // 3) * 3
        for r in range(start_row, start_row + 3):
            for c in range(start_col, start_col + 3):
                candidates[r][c].discard(value)
        candidates[row][col] = set()

    def last_empty_method():
        change = False
        points = 0
        units = []
        for i in range(9):
            units.append([(i, c) for c in range(9)])
        for i in range(9):
            units.append([(r, i) for r in range(9)])
        for i in range(9):
            start_row, start_col = (i // 3) * 3, (i % 3) * 3
            units.append([(r, c) for r in range(start_row, start_row + 3) for c in range(start_col, start_col + 3)])
        for unit in units:
            values = [board[r][c] for r, c in unit]
            if values.count(0) == 1:
                missing = [n for n in range(1, 10) if n not in values][0]
                for r, c in unit:
                    if board[r][c] == 0:
                        board[r][c] = missing
                        update_after_move(r, c, missing)
                        change = True
                        points += 1
                        break
        return change, points

    def single_choice_method():
        change = False
        points = 0
        for r in range(9):
            for c in range(9):
                if board[r][c] == 0:
                    options = [value for value in range(1, 10) if is_valid(board, r, c, value)]
                    if len(options) == 1:
                        value = options[0]
                        board[r][c] = value
                        update_after_move(r, c, value)
                        change = True
                        points += 2
        return change, points

    def single_position_method():
        change = False
        points = 0
        for unit in all_groups():
            for value in range(1, 10):
                if any(board[r][c] == value for r, c in unit):
                    continue
                positions = [(r, c) for r, c in unit if board[r][c] == 0 and is_valid(board, r, c, value)]
                if len(positions) == 1:
                    row, col = positions[0]
                    board[row][col] = value
                    update_after_move(row, col, value)
                    change = True
                    points += 3
        return change, points

    def candidate_transfer_method():
        change = False
        points = 0
        for r in range(9):
            for c in range(9):
                if board[r][c] == 0 and len(candidates[r][c]) == 1:
                    value = next(iter(candidates[r][c]))
                    board[r][c] = value
                    update_after_move(r, c, value)
                    change = True
                    points += 3
        return change, points

    def visible_pair_method():
        change = False
        points = 0
        for unit in all_groups():
            pairs = [(r, c) for r, c in unit if len(candidates[r][c]) == 2]
            for i in range(len(pairs)):
                for j in range(i + 1, len(pairs)):
                    r1, c1 = pairs[i]
                    r2, c2 = pairs[j]
                    k1 = candidates[r1][c1]
                    k2 = candidates[r2][c2]
                    if k1 == k2:
                        eliminated = False
                        for r, c in unit:
                            if (r, c) not in ((r1, c1), (r2, c2)):
                                if not candidates[r][c].isdisjoint(k1):
                                    candidates[r][c] -= k1
                                    eliminated = True
                        if eliminated:
                            change = True
                            points += 4
        return change, points

    def direct_pair_method():
        change = False
        points = 0
        for block_index in range(9):
            start_row, start_col = (block_index // 3) * 3, (block_index % 3) * 3
            for value in range(1, 10):
                positions = [
                    (r, c) for r in range(start_row, start_row + 3) for c in range(start_col, start_col + 3)
                    if value in candidates[r][c]
                ]
                if 2 <= len(positions) <= 3:
                    if all(position[0] == positions[0][0] for position in positions):
                        row = positions[0][0]
                        eliminated = False
                        for c in range(9):
                            if not (start_col <= c < start_col + 3) and value in candidates[row][c]:
                                candidates[row][c].discard(value)
                                eliminated = True
                        if eliminated:
                            change = True
                            points += 6
                    elif all(position[1] == positions[0][1] for position in positions):
                        col = positions[0][1]
                        eliminated = False
                        for r in range(9):
                            if not (start_row <= r < start_row + 3) and value in candidates[r][col]:
                                candidates[r][col].discard(value)
                                eliminated = True
                        if eliminated:
                            change = True
                            points += 6
        return change, points

    def hidden_pair_method():
        change = False
        points = 0
        for unit in all_groups():
            for value_1 in range(1, 10):
                for value_2 in range(value_1 + 1, 10):
                    positions = [(r, c) for r, c in unit if value_1 in candidates[r][c] and value_2 in candidates[r][c]]
                    if len(positions) == 2:
                        value_1_count = sum(1 for r, c in unit if value_1 in candidates[r][c])
                        value_2_count = sum(1 for r, c in unit if value_2 in candidates[r][c])
                        if value_1_count == 2 and value_2_count == 2:
                            reduced = False
                            for r, c in positions:
                                if len(candidates[r][c]) > 2:
                                    candidates[r][c] = {value_1, value_2}
                                    reduced = True
                            if reduced:
                                change = True
                                points += 10
        return change, points

    def visible_triple_method():
        change = False
        points = 0
        for unit in all_groups():
            cells = [(r, c) for r, c in unit if 1 < len(candidates[r][c]) <= 3]
            if len(cells) < 3:
                continue
            for i in range(len(cells)):
                for j in range(i + 1, len(cells)):
                    for k in range(j + 1, len(cells)):
                        r1, c1 = cells[i]
                        r2, c2 = cells[j]
                        r3, c3 = cells[k]
                        union = candidates[r1][c1] | candidates[r2][c2] | candidates[r3][c3]
                        if len(union) == 3:
                            eliminated = False
                            for r, c in unit:
                                if (r, c) not in ((r1, c1), (r2, c2), (r3, c3)):
                                    if not candidates[r][c].isdisjoint(union):
                                        candidates[r][c] -= union
                                        eliminated = True
                            if eliminated:
                                change = True
                                points += 15
        return change, points

    def x_wing_method():
        change = False
        points = 0
        for value in range(1, 10):
            rows = []
            for r in range(9):
                columns = [c for c in range(9) if value in candidates[r][c]]
                if len(columns) == 2:
                    rows.append((r, columns))
            for i in range(len(rows)):
                for j in range(i + 1, len(rows)):
                    r1, c1 = rows[i]
                    r2, c2 = rows[j]
                    if c1 == c2:
                        eliminated = False
                        for r_idx in range(9):
                            if r_idx != r1 and r_idx != r2:
                                for c_idx in c1:
                                    if value in candidates[r_idx][c_idx]:
                                        candidates[r_idx][c_idx].discard(value)
                                        eliminated = True
                        if eliminated:
                            change = True
                            points += 25

            column_pairs = []
            for c in range(9):
                rows_for_value = [r for r in range(9) if value in candidates[r][c]]
                if len(rows_for_value) == 2:
                    column_pairs.append((c, rows_for_value))
            for i in range(len(column_pairs)):
                for j in range(i + 1, len(column_pairs)):
                    c1, r1 = column_pairs[i]
                    c2, r2 = column_pairs[j]
                    if r1 == r2:
                        eliminated = False
                        for c_idx in range(9):
                            if c_idx != c1 and c_idx != c2:
                                for r_idx in r1:
                                    if value in candidates[r_idx][c_idx]:
                                        candidates[r_idx][c_idx].discard(value)
                                        eliminated = True
                        if eliminated:
                            change = True
                            points += 25
        return change, points

    step_limit = 200
    for _ in range(step_limit):
        ok, gained = last_empty_method()
        if ok:
            score += gained
            continue

        ok, gained = single_choice_method()
        if ok:
            score += gained
            continue

        ok, gained = single_position_method()
        if ok:
            score += gained
            continue

        if not candidates_active:
            refresh_candidates()
            candidates_active = True

        overall_change = False
        ok, gained = direct_pair_method()
        if ok:
            score += gained
            overall_change = True
        ok, gained = visible_pair_method()
        if ok:
            score += gained
            overall_change = True
        ok, gained = hidden_pair_method()
        if ok:
            score += gained
            overall_change = True
        ok, gained = visible_triple_method()
        if ok:
            score += gained
            overall_change = True
        ok, gained = x_wing_method()
        if ok:
            score += gained
            overall_change = True

        ok, gained = candidate_transfer_method()
        if ok:
            score += gained
            overall_change = True

        if overall_change:
            continue
        break

    empty_count = sum(row.count(0) for row in board)
    if empty_count == 0:
        return score, True

    penalized_score = score + 50 + (empty_count * 5)
    return penalized_score, False


def generate_game(cells_to_remove=40):
    if cells_to_remove < 20:
        minimum_score = max(1, cells_to_remove // 3)
    elif cells_to_remove < 35:
        minimum_score = cells_to_remove // 2
    elif cells_to_remove < 50:
        minimum_score = cells_to_remove // 2 + 5
    else:
        minimum_score = 100

    print(f"Searching for Sudoku with {cells_to_remove} holes and min. score {minimum_score}...")
    attempt = 0
    last_puzzle = None
    last_solution = None
    last_score = 0

    while attempt < 50:
        attempt += 1
        board = [[0] * 9 for _ in range(9)]
        fill_board(board)
        full_solution = [row[:] for row in board]
        puzzle = remove_numbers([row[:] for row in board], cells_to_remove)
        score, is_solvable = determine_complexity(puzzle)

        if is_solvable and score >= minimum_score:
            print(f"Found one! Attempt {attempt}, score: {score}")
            return puzzle, full_solution, score

        if not is_solvable:
            print(f"Attempt {attempt}: Sudoku is not logically solvable. Trying again...")

        last_puzzle = puzzle
        last_solution = full_solution
        last_score = score

    print("Warning: Could not find a sufficiently difficult Sudoku within the limit. Returning the last one found.")
    return last_puzzle, last_solution, last_score


# Compatibility aliases for the previous Czech API.
je_valid = is_valid
spocitej_reseni = count_solutions
doplneni_pole = fill_board
odeber_cisla = remove_numbers
je_vyreseno = is_solved
urceni_slozitosti = determine_complexity
vygeneruj_hru = generate_game

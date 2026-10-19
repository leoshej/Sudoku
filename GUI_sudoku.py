"""Sudoku GUI using Pygame."""

import pygame
import sys
import time

try:
    import sudoku
except ImportError:
    print("ERROR: 'sudoku.py' was not found!")
    sys.exit()

SCREEN_WIDTH = 600
SCREEN_HEIGHT = 750
GRID_SIZE = 540
CELL_SIZE = GRID_SIZE // 9
MARGIN = (SCREEN_WIDTH - GRID_SIZE) // 2
START_Y = 80

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (200, 200, 200)
BLUE = (50, 150, 255)
DARK_BLUE = (0, 100, 200)
RED = (220, 20, 60)
GREEN = (34, 139, 34)
ORANGE = (255, 165, 0)
YELLOW = (255, 215, 0)
USER_COLOR = (0, 0, 150)
HIGHLIGHT = (255, 255, 200)
BG_COLOR = (240, 248, 255)
PENCIL_COLOR = (100, 100, 100)

pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Sudoku")

font_numbers = pygame.font.SysFont('arial', 40, bold=True)
font_pencil = pygame.font.SysFont('arial', 15, bold=True)
font_ui = pygame.font.SysFont('arial', 25)
font_title = pygame.font.SysFont('comicsans', 60)
font_info = pygame.font.SysFont('arial', 20)
font_gameover = pygame.font.SysFont('arial', 50, bold=True)


class Button:
    """Interactive button."""

    def __init__(self, text, x, y, w, h, color, hover_color):
        self.text = text
        self.rect = pygame.Rect(x, y, w, h)
        self.base_color = color
        self.hover_color = hover_color
        self.current_color = color
        self.active = False

    def update_text(self, new_text):
        self.text = new_text

    def update_color(self, new_color, new_hover):
        self.base_color = new_color
        self.hover_color = new_hover

    def set_active(self, is_active):
        self.active = is_active
        if self.active:
            self.current_color = YELLOW
        else:
            self.current_color = self.base_color

    def draw(self, screen):
        draw_color = YELLOW if self.active else self.current_color

        pygame.draw.rect(screen, (50, 50, 50),
                        (self.rect.x + 2, self.rect.y + 2, self.rect.w, self.rect.h),
                        border_radius=12)
        pygame.draw.rect(screen, draw_color, self.rect, border_radius=12)
        pygame.draw.rect(screen, BLACK, self.rect, 2, border_radius=12)

        text_color = BLACK if self.active else WHITE
        text_surf = font_ui.render(self.text, True, text_color)
        text_rect = text_surf.get_rect(center=self.rect.center)
        screen.blit(text_surf, text_rect)

    def check_hover(self, mouse_pos):
        if not self.active:
            self.current_color = self.hover_color if self.rect.collidepoint(mouse_pos) else self.base_color

    def is_clicked(self, mouse_pos):
        return self.rect.collidepoint(mouse_pos)


def draw_sudoku_grid(screen, current_grid, fixed_grid, solution_grid, pencil_grid, selected_cell):
    """Render the full Sudoku board."""
    pygame.draw.rect(screen, WHITE, (MARGIN, START_Y, GRID_SIZE, GRID_SIZE))

    if selected_cell:
        row, col = selected_cell
        x = MARGIN + col * CELL_SIZE
        y = START_Y + row * CELL_SIZE
        pygame.draw.rect(screen, HIGHLIGHT, (x, y, CELL_SIZE, CELL_SIZE))

    for row in range(9):
        for col in range(9):
            value = current_grid[row][col]
            x_cell = MARGIN + col * CELL_SIZE
            y_cell = START_Y + row * CELL_SIZE

            if value != 0:
                if fixed_grid[row][col] != 0:
                    color = BLACK
                else:
                    color = RED

                text = font_numbers.render(str(value), True, color)
                x_pos = x_cell + (CELL_SIZE // 2 - text.get_width() // 2)
                y_pos = y_cell + (CELL_SIZE // 2 - text.get_height() // 2) + 2
                screen.blit(text, (x_pos, y_pos))
            else:
                marks = pencil_grid[row][col]
                if marks:
                    for mark in marks:
                        row_in_cell = (mark - 1) // 3
                        col_in_cell = (mark - 1) % 3
                        offset_x = col_in_cell * (CELL_SIZE // 3) + (CELL_SIZE // 6)
                        offset_y = row_in_cell * (CELL_SIZE // 3) + (CELL_SIZE // 6)
                        text = font_pencil.render(str(mark), True, PENCIL_COLOR)
                        screen.blit(text, (x_cell + offset_x - text.get_width() // 2,
                                          y_cell + offset_y - text.get_height() // 2))

    for i in range(10):
        thickness = 4 if i % 3 == 0 else 1
        color = BLACK if i % 3 == 0 else (160, 160, 160)

        pygame.draw.line(screen, color,
                        (MARGIN, START_Y + i * CELL_SIZE),
                        (MARGIN + GRID_SIZE, START_Y + i * CELL_SIZE),
                        thickness)

        pygame.draw.line(screen, color,
                        (MARGIN + i * CELL_SIZE, START_Y),
                        (MARGIN + i * CELL_SIZE, START_Y + GRID_SIZE),
                        thickness)

    pygame.draw.rect(screen, BLACK, (MARGIN, START_Y, GRID_SIZE, GRID_SIZE), 4)


def main():
    clock = pygame.time.Clock()
    running = True
    game_state = "MENU"

    current_grid = None
    fixed_grid = None
    solution_grid = None
    pencil_grid = [[set() for _ in range(9)] for _ in range(9)]

    selected_cell = None
    current_score = 0
    lives = 3
    total_errors = 0

    pencil_mode = False
    start_time = 0
    elapsed_time = 0

    difficulty_levels = ["Easy", "Medium", "Hard"]
    holes_map = [30, 45, 54]
    colors_map = [GREEN, BLUE, ORANGE]
    current_diff_idx = 1

    btn_start = Button("Start Game", 150, 250, 300, 60, BLUE, DARK_BLUE)
    btn_diff = Button(f"Difficulty: {difficulty_levels[current_diff_idx]}", 150, 350, 300, 60,
                     colors_map[current_diff_idx], (100, 100, 100))
    btn_quit = Button("Quit", 150, 450, 300, 60, RED, (200, 0, 0))

    btn_menu = Button("Back", 20, 10, 80, 40, GRAY, (150, 150, 150))
    btn_pencil = Button("Pencil", 480, 10, 100, 40, GRAY, (180, 180, 180))

    btn_gameover_menu = Button("Back to Menu", 150, 400, 300, 60, BLUE, DARK_BLUE)
    btn_win_menu = Button("Back to Menu", 150, 500, 300, 60, BLUE, DARK_BLUE)

    while running:
        mouse_pos = pygame.mouse.get_pos()
        screen.fill(BG_COLOR)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if event.type == pygame.MOUSEBUTTONDOWN:
                if game_state == "MENU":
                    if btn_start.is_clicked(mouse_pos):
                        screen.fill(BG_COLOR)
                        msg = font_title.render("Generating...", True, BLACK)
                        screen.blit(msg, (180, 300))
                        pygame.display.flip()

                        holes_count = holes_map[current_diff_idx]
                        puzzle_grid, solution_grid_value, score = sudoku.vygeneruj_hru(cells_to_remove=holes_count)

                        current_grid = [row[:] for row in puzzle_grid]
                        fixed_grid = [row[:] for row in puzzle_grid]
                        solution_grid = solution_grid_value
                        pencil_grid = [[set() for _ in range(9)] for _ in range(9)]

                        pencil_mode = False
                        btn_pencil.set_active(False)
                        current_score = score
                        lives = 3
                        total_errors = 0

                        start_time = time.time()
                        game_state = "GAME"
                        selected_cell = None

                    elif btn_diff.is_clicked(mouse_pos):
                        current_diff_idx = (current_diff_idx + 1) % 3
                        btn_diff.update_text(f"Difficulty: {difficulty_levels[current_diff_idx]}")
                        btn_diff.update_color(colors_map[current_diff_idx], (100, 100, 100))

                    elif btn_quit.is_clicked(mouse_pos):
                        running = False

                elif game_state == "GAME":
                    if btn_menu.is_clicked(mouse_pos):
                        game_state = "MENU"
                    elif btn_pencil.is_clicked(mouse_pos):
                        pencil_mode = not pencil_mode
                        btn_pencil.set_active(pencil_mode)

                    x, y = mouse_pos
                    if MARGIN <= x <= MARGIN + GRID_SIZE and START_Y <= y <= START_Y + GRID_SIZE:
                        col = (x - MARGIN) // CELL_SIZE
                        row = (y - START_Y) // CELL_SIZE
                        selected_cell = (row, col)
                    else:
                        selected_cell = None

                elif game_state == "GAMEOVER":
                    if btn_gameover_menu.is_clicked(mouse_pos):
                        game_state = "MENU"

                elif game_state == "WIN":
                    if btn_win_menu.is_clicked(mouse_pos):
                        game_state = "MENU"

            if event.type == pygame.KEYDOWN and game_state == "GAME":
                if selected_cell:
                    row, col = selected_cell
                    if fixed_grid[row][col] == 0:
                        key_num = None
                        key_map = {
                            pygame.K_1: 1, pygame.K_KP1: 1,
                            pygame.K_2: 2, pygame.K_KP2: 2,
                            pygame.K_3: 3, pygame.K_KP3: 3,
                            pygame.K_4: 4, pygame.K_KP4: 4,
                            pygame.K_5: 5, pygame.K_KP5: 5,
                            pygame.K_6: 6, pygame.K_KP6: 6,
                            pygame.K_7: 7, pygame.K_KP7: 7,
                            pygame.K_8: 8, pygame.K_KP8: 8,
                            pygame.K_9: 9, pygame.K_KP9: 9
                        }

                        if event.key in key_map:
                            key_num = key_map[event.key]

                            if pencil_mode:
                                if key_num in pencil_grid[row][col]:
                                    pencil_grid[row][col].remove(key_num)
                                else:
                                    pencil_grid[row][col].add(key_num)
                            else:
                                if key_num == solution_grid[row][col]:
                                    current_grid[row][col] = key_num
                                    fixed_grid[row][col] = key_num
                                    pencil_grid[row][col] = set()

                                    if sudoku.je_vyreseno(current_grid):
                                        elapsed_time = time.time() - start_time
                                        game_state = "WIN"
                                else:
                                    current_grid[row][col] = key_num
                                    lives -= 1
                                    total_errors += 1
                                    if lives <= 0:
                                        elapsed_time = time.time() - start_time
                                        game_state = "GAMEOVER"

                        if event.key == pygame.K_BACKSPACE or event.key == pygame.K_DELETE:
                            current_grid[row][col] = 0
                            pencil_grid[row][col] = set()

                if selected_cell:
                    row, col = selected_cell
                    if event.key == pygame.K_UP:
                        row = max(0, row - 1)
                    if event.key == pygame.K_DOWN:
                        row = min(8, row + 1)
                    if event.key == pygame.K_LEFT:
                        col = max(0, col - 1)
                    if event.key == pygame.K_RIGHT:
                        col = min(8, col + 1)
                    selected_cell = (row, col)

        if game_state == "MENU":
            title = font_title.render("Sudoku", True, BLACK)
            screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 100))
            for btn in [btn_start, btn_diff, btn_quit]:
                btn.check_hover(mouse_pos)
                btn.draw(screen)

        elif game_state == "GAME":
            elapsed_time = time.time() - start_time

            btn_menu.check_hover(mouse_pos)
            btn_menu.draw(screen)
            btn_pencil.check_hover(mouse_pos)
            btn_pencil.draw(screen)

            minutes = int(elapsed_time // 60)
            seconds = int(elapsed_time % 60)
            timer_text = f"Time: {minutes:02d}:{seconds:02d}"
            surf_timer = font_info.render(timer_text, True, DARK_BLUE)
            screen.blit(surf_timer, (20, 60))

            diff_text = difficulty_levels[current_diff_idx]
            score_text = f"Complexity: {current_score}"
            lives_text = f"Mistakes: {3 - lives}/3"

            lives_color = RED if lives == 1 else DARK_BLUE

            surf_diff = font_info.render(diff_text, True, BLACK)
            surf_score = font_info.render(score_text, True, BLACK)
            surf_lives = font_info.render(lives_text, True, lives_color)

            screen.blit(surf_diff, (SCREEN_WIDTH // 2 - surf_diff.get_width() // 2, 10))
            screen.blit(surf_score, (SCREEN_WIDTH // 2 - surf_score.get_width() // 2, 35))
            screen.blit(surf_lives, (SCREEN_WIDTH // 2 - surf_lives.get_width() // 2, 60))

            draw_sudoku_grid(screen, current_grid, fixed_grid, solution_grid, pencil_grid, selected_cell)

        elif game_state == "GAMEOVER":
            txt_over = font_gameover.render("GAME OVER", True, RED)
            txt_msg = font_ui.render("You ran out of lives!", True, BLACK)

            screen.blit(txt_over, (SCREEN_WIDTH // 2 - txt_over.get_width() // 2, 250))
            screen.blit(txt_msg, (SCREEN_WIDTH // 2 - txt_msg.get_width() // 2, 320))

            btn_gameover_menu.check_hover(mouse_pos)
            btn_gameover_menu.draw(screen)

        elif game_state == "WIN":
            txt_win = font_gameover.render("CONGRATULATIONS!", True, GREEN)
            txt_msg = font_ui.render("You solved the Sudoku!", True, BLACK)

            minutes = int(elapsed_time // 60)
            seconds = int(elapsed_time % 60)
            time_text = f"Time: {minutes:02d}:{seconds:02d}"
            txt_time = font_title.render(time_text, True, DARK_BLUE)

            errors_text = f"Mistakes: {total_errors}"
            txt_errors = font_ui.render(errors_text, True, BLACK)

            screen.blit(txt_win, (SCREEN_WIDTH // 2 - txt_win.get_width() // 2, 200))
            screen.blit(txt_msg, (SCREEN_WIDTH // 2 - txt_msg.get_width() // 2, 280))
            screen.blit(txt_time, (SCREEN_WIDTH // 2 - txt_time.get_width() // 2, 340))
            screen.blit(txt_errors, (SCREEN_WIDTH // 2 - txt_errors.get_width() // 2, 430))

            btn_win_menu.check_hover(mouse_pos)
            btn_win_menu.draw(screen)

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
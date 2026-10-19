"""
SUDOKU GUI - PYGAME INTERFACE
==========================================
Interactive Sudoku game using the pygame library.
The player fills in numbers and receives feedback on correctness.

Key features:
- Graphical grid display
- Pencil marks
- Life system (3 mistakes = game over)
- Timer and score counter
- Menu with difficulty selection

Author: Leoš Hejlek
Date: 2026-02-11
"""

import pygame
import sys
import copy
import time

# --- LOAD LOGIC (Sudoku module) ---
try:
    import sudoku
except ImportError:
    print("ERROR: 'sudoku.py' was not found!")
    sys.exit()

# ============================================================================
# GAME CONFIGURATION
# ============================================================================

# Window dimensions (in pixels)
SCREEN_WIDTH = 600      # Window width
SCREEN_HEIGHT = 750     # Window height (includes UI elements at the top)
GRID_SIZE = 540         # Grid size (9x9)
CELL_SIZE = GRID_SIZE // 9  # Size of a single cell (60x60)
MARGIN = (SCREEN_WIDTH - GRID_SIZE) // 2  # Horizontal margin
START_Y = 80            # Grid position from the top edge

# ============================================================================
# COLORS (RGB)
# ============================================================================

WHITE = (255, 255, 255)     # White - cell background
BLACK = (0, 0, 0)           # Black - numbers and lines
GRAY = (200, 200, 200)      # Gray - buttons
BLUE = (50, 150, 255)       # Blue - primary buttons
DARK_BLUE = (0, 100, 200)   # Dark blue - call, score
RED = (220, 20, 60)         # Red - error, mistakes
GREEN = (34, 139, 34)       # Green - "easy"
ORANGE = (255, 165, 0)      # Orange - "hard"
YELLOW = (255, 215, 0)      # Gold - active button
USER_COLOR = (0, 0, 150)    # Dark blue - correctly filled numbers
HIGHLIGHT = (255, 255, 200) # Light yellow - highlighting selected
BG_COLOR = (240, 248, 255)  # Transparent blue - background
PENCIL_COLOR = (100, 100, 100)

pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Sudoku")

# Fonts (various sizes and styles)
font_numbers = pygame.font.SysFont('arial', 40, bold=True)     # Numbers in cells
font_pencil = pygame.font.SysFont('arial', 15, bold=True)  # Notes (pencil)
font_ui = pygame.font.SysFont('arial', 25)                 # Buttons
font_title = pygame.font.SysFont('comicsans', 60)         # Game title
font_info = pygame.font.SysFont('arial', 20)              # Information (time, score)
font_gameover = pygame.font.SysFont('arial', 50, bold=True)  # Game over

# ============================================================================
# BUTTON CLASS - INTERACTIVE BUTTON
# ============================================================================

class Button:
    """
    Represents an interactive button with effects when hovered by the mouse.
    
    Properties:
    - text: Button label
    - rect: Position and size
    - colors: Base and hover color
    - active state: Highlighting when selected
    """
    def __init__(self, text, x, y, w, h, color, hover_color):
        """
        Creates a new button.
        
        Args:
            text: Text on the button
            x, y: Position (top-left corner)
            w, h: Width and height
            color: Base color
            hover_color: Color when mouse is over the button
        """
        self.text = text
        self.rect = pygame.Rect(x, y, w, h)
        self.base_color = color
        self.hover_color = hover_color
        self.current_color = color
        self.active = False  # Whether the button is active (selected)

    def update_text(self, new_text):
        """Change the text on the button"""
        self.text = new_text

    def update_color(self, new_color, new_hover):
        """Change the button colors"""
        self.base_color = new_color
        self.hover_color = new_hover

    def set_active(self, is_active):
        """
        Set the active state of the button.
        Active button is highlighted in yellow.
        """
        self.active = is_active
        if self.active:
            self.current_color = YELLOW
        else:
            self.current_color = self.base_color

    def draw(self, screen):
        """
        Draw the button on the screen.
        
        Draws:
        1. Shadow (dark offset)
        2. Main button
        3. Border
        4. Text
        """
        draw_color = YELLOW if self.active else self.current_color
        
        # Shadow
        pygame.draw.rect(screen, (50, 50, 50), 
                        (self.rect.x + 2, self.rect.y + 2, self.rect.w, self.rect.h), 
                        border_radius=12)
        # Main button
        pygame.draw.rect(screen, draw_color, self.rect, border_radius=12)
        # Border
        pygame.draw.rect(screen, BLACK, self.rect, 2, border_radius=12)
        
        # Text
        text_color = BLACK if self.active else WHITE
        text_surf = font_ui.render(self.text, True, text_color)
        text_rect = text_surf.get_rect(center=self.rect.center)
        screen.blit(text_surf, text_rect)

    def check_hover(self, mouse_pos):
        """Check if the mouse is over the button and change color"""
        if not self.active:
            self.current_color = self.hover_color if self.rect.collidepoint(mouse_pos) else self.base_color

    def is_clicked(self, mouse_pos):
        """Check if the button was clicked"""
        return self.rect.collidepoint(mouse_pos)

# ============================================================================
# FUNCTIONS FOR DRAWING THE GRID
# ============================================================================

def draw_sudoku_grid(screen, current_grid, fixed_grid, solution_grid, pencil_grid, selected_cell):
    """
    Draws the complete Sudoku grid with content.
    
    DRAWS:
    1. Background (white cells)
    2. Highlighting of the selected cell
    3. Numbers in correct colors
    4. Notes (pencil) - small numbers
    5. Grid lines (thin between cells, thick between boxes)
    6. Outer border
    
    Args:
        screen: Pygame surface for drawing
        current_grid: Current game state
        fixed_grid: Numbers that are locked (given + correctly filled)
        solution_grid: Correct solution
        pencil_grid: Notes in cells
        selected_cell: Currently selected cell (r, c) or None
    """
    # Draw white background of the grid
    pygame.draw.rect(screen, WHITE, (MARGIN, START_Y, GRID_SIZE, GRID_SIZE))
    
    # Highlight the selected cell
    if selected_cell:
        r, c = selected_cell
        x = MARGIN + c * CELL_SIZE
        y = START_Y + r * CELL_SIZE
        pygame.draw.rect(screen, HIGHLIGHT, (x, y, CELL_SIZE, CELL_SIZE))

    # === DRAWING CELL CONTENT ===
    for r in range(9):
        for c in range(9):
            val = current_grid[r][c]
            x_cell = MARGIN + c * CELL_SIZE
            y_cell = START_Y + r * CELL_SIZE

            # A) LARGE NUMBER (if the cell is filled)
            if val != 0:
                # BLACK - was entered (in fixed_grid)
                # RED - user entered it incorrectly
                if fixed_grid[r][c] != 0:
                    color = BLACK  # Given or correctly filled
                else:
                    color = RED    # User entered incorrectly

                text = font_numbers.render(str(val), True, color)
                x_pos = x_cell + (CELL_SIZE // 2 - text.get_width() // 2)
                y_pos = y_cell + (CELL_SIZE // 2 - text.get_height() // 2) + 2
                screen.blit(text, (x_pos, y_pos))
            
            # B) PENCIL NOTES (small numbers)
            else:
                marks = pencil_grid[r][c]
                if marks:
                    for mark in marks:
                        # Position of the small number in the cell
                        # A 60x60 cell is divided 3x3, so it's 20x20 for each number
                        row_in_cell = (mark - 1) // 3
                        col_in_cell = (mark - 1) % 3
                        offset_x = col_in_cell * (CELL_SIZE // 3) + (CELL_SIZE // 6)
                        offset_y = row_in_cell * (CELL_SIZE // 3) + (CELL_SIZE // 6)
                        text = font_pencil.render(str(mark), True, PENCIL_COLOR)
                        screen.blit(text, (x_cell + offset_x - text.get_width()//2, 
                                          y_cell + offset_y - text.get_height()//2))

    # === DRAWING THE GRID (LINES) ===
    for i in range(10):
        # Every 3rd line (border of boxes) is thicker
        thickness = 4 if i % 3 == 0 else 1
        color = BLACK if i % 3 == 0 else (160, 160, 160)
        
        # Horizontal lines
        pygame.draw.line(screen, color, 
                        (MARGIN, START_Y + i * CELL_SIZE), 
                        (MARGIN + GRID_SIZE, START_Y + i * CELL_SIZE), 
                        thickness)
        
        # Vertical lines
        pygame.draw.line(screen, color, 
                        (MARGIN + i * CELL_SIZE, START_Y), 
                        (MARGIN + i * CELL_SIZE, START_Y + GRID_SIZE), 
                        thickness)
    
    # Outer border (thick)
    pygame.draw.rect(screen, BLACK, (MARGIN, START_Y, GRID_SIZE, GRID_SIZE), 4)


# ============================================================================
# MAIN GAME LOOP
# ============================================================================

def main():
    """
    Main game loop. Manages:
    - Action detection (keyboard, mouse)
    - State changes (MENU -> GAME -> WIN/GAMEOVER)
    - Game logic (validating moves, calculating scores...) 
    - Rendering (according to the current state)
    """
    clock = pygame.time.Clock()  # For FPS
    running = True
    game_state = "MENU"  # States: MENU, GAME, GAMEOVER, WIN
    
    # === GAME DATA ===
    current_grid = None        # Current game state
    fixed_grid = None          # What is locked
    solution_grid = None       # Correct solution
    pencil_grid = [[set() for _ in range(9)] for _ in range(9)]  # Notes
    
    selected_cell = None       # Selected cell (r, c)
    current_score = 0          # Score (difficulty of Sudoku)
    lives = 3                  # Number of lives (max 3 mistakes)
    total_errors = 0           # Total number of mistakes
    
    pencil_mode = False        # Whether pencil mode is on
    
    # === TIMER ===
    start_time = 0
    elapsed_time = 0
    
    # === DIFFICULTY SETTINGS ===
    difficulty_levels = ["Easy", "Medium", "Hard"]
    holes_map = [30, 45, 54]  # Number of holes by difficulty
    colors_map = [GREEN, BLUE, ORANGE]  # Colors by difficulty
    current_diff_idx = 1

    # === BUTTONS ===
    # MENU buttons
    btn_start = Button("Start Game", 150, 250, 300, 60, BLUE, DARK_BLUE)
    btn_diff = Button(f"Difficulty: {difficulty_levels[current_diff_idx]}", 150, 350, 300, 60, 
                     colors_map[current_diff_idx], (100, 100, 100))
    btn_quit = Button("Quit", 150, 450, 300, 60, RED, (200, 0, 0))
    
    # GAME buttons
    btn_menu = Button("Back", 20, 10, 80, 40, GRAY, (150, 150, 150))
    btn_pencil = Button("Pencil", 480, 10, 100, 40, GRAY, (180, 180, 180))

    # GAMEOVER and WIN buttons
    btn_gameover_menu = Button("Back to Menu", 150, 400, 300, 60, BLUE, DARK_BLUE)
    btn_win_menu = Button("Back to Menu", 150, 500, 300, 60, BLUE, DARK_BLUE)

    # === GAME LOOP ===
    while running:
        mouse_pos = pygame.mouse.get_pos()
        screen.fill(BG_COLOR)

        # === ACTION DETECTION ===
        for event in pygame.event.get():
            # Close window
            if event.type == pygame.QUIT:
                running = False
            
            # === MOUSE CLICK ===
            if event.type == pygame.MOUSEBUTTONDOWN:
                # MENU - Button clicks
                if game_state == "MENU":
                    if btn_start.is_clicked(mouse_pos):
                        # Generate new game
                        screen.fill(BG_COLOR)
                        msg = font_title.render("Generating...", True, BLACK)
                        screen.blit(msg, (180, 300))
                        pygame.display.flip()
                        
                        # Generate new Sudoku with the selected difficulty
                        holes_count = holes_map[current_diff_idx]
                        puzzle_grid, solution_grid_value, score = sudoku.vygeneruj_hru(pocet_dier=holes_count)
                        
                        # Initialize game grid
                        current_grid = [row[:] for row in puzzle_grid]
                        fixed_grid = [row[:] for row in puzzle_grid]  # What is locked
                        solution_grid = solution_grid_value
                        pencil_grid = [[set() for _ in range(9)] for _ in range(9)]
                        
                        # Reset states
                        pencil_mode = False
                        btn_pencil.set_active(False)
                        current_score = score
                        lives = 3
                        total_errors = 0
                        
                        # Start timer
                        start_time = time.time()
                        
                        game_state = "GAME"
                        selected_cell = None
                    
                    elif btn_diff.is_clicked(mouse_pos):
                        # Change difficulty (Easy -> Medium -> Hard -> Easy)
                        current_diff_idx = (current_diff_idx + 1) % 3
                        btn_diff.update_text(f"Difficulty: {difficulty_levels[current_diff_idx]}")
                        btn_diff.update_color(colors_map[current_diff_idx], (100, 100, 100))

                    elif btn_quit.is_clicked(mouse_pos):
                        running = False

                # GAME - Click on buttons or cells
                elif game_state == "GAME":
                    if btn_menu.is_clicked(mouse_pos):
                        # Back to menu
                        game_state = "MENU"
                    elif btn_pencil.is_clicked(mouse_pos):
                        # Toggle pencil mode
                        pencil_mode = not pencil_mode
                        btn_pencil.set_active(pencil_mode)
                    
                    # Click on grid - select cell
                    x, y = mouse_pos
                    if MARGIN <= x <= MARGIN + GRID_SIZE and START_Y <= y <= START_Y + GRID_SIZE:
                        col = (x - MARGIN) // CELL_SIZE
                        row = (y - START_Y) // CELL_SIZE
                        selected_cell = (row, col)
                    else:
                        selected_cell = None
                
                # GAMEOVER - Click on Menu button
                elif game_state == "GAMEOVER":
                    if btn_gameover_menu.is_clicked(mouse_pos):
                        game_state = "MENU"
                
                # WIN - Click on Menu button
                elif game_state == "WIN":
                    if btn_win_menu.is_clicked(mouse_pos):
                        game_state = "MENU"

            # === KEYBOARD (ONLY IN GAME STATE) ===
            if event.type == pygame.KEYDOWN and game_state == "GAME":
                if selected_cell:
                    r, c = selected_cell
                    # Allow input only if the cell is not locked
                    if fixed_grid[r][c] == 0:
                        
                        key_num = None
                        # Mapping of keys 1-9
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
                                # PENCIL MODE: Toggle note (without validation)
                                if key_num in pencil_grid[r][c]:
                                    pencil_grid[r][c].remove(key_num)
                                else:
                                    pencil_grid[r][c].add(key_num)
                            else:
                                # PEN MODE: Fill in the number and check
                                if key_num == solution_grid[r][c]:
                                    # ✓ CORRECT - lock the cell
                                    current_grid[r][c] = key_num
                                    fixed_grid[r][c] = key_num  # Locking
                                    pencil_grid[r][c] = set()  # Clear notes
                                    
                                    # Check for win
                                    if sudoku.je_vyreseno(current_grid):
                                        elapsed_time = time.time() - start_time
                                        game_state = "WIN"
                                else:
                                    # ✗ ERROR - deduct a life
                                    current_grid[r][c] = key_num
                                    lives -= 1
                                    total_errors += 1
                                    if lives <= 0:
                                        elapsed_time = time.time() - start_time
                                        game_state = "GAMEOVER"

                        # Delete the cell (Backspace/Delete)
                        if event.key == pygame.K_BACKSPACE or event.key == pygame.K_DELETE:
                            current_grid[r][c] = 0
                            pencil_grid[r][c] = set()

                # Navigation with arrow keys
                if selected_cell:
                    r, c = selected_cell
                    if event.key == pygame.K_UP:
                        r = max(0, r - 1)
                    if event.key == pygame.K_DOWN:
                        r = min(8, r + 1)
                    if event.key == pygame.K_LEFT:
                        c = max(0, c - 1)
                    if event.key == pygame.K_RIGHT:
                        c = min(8, c + 1)
                    selected_cell = (r, c)

        # === RENDERING (ACCORDING TO STATE) ===
        if game_state == "MENU":
            # MENU screen
            title = font_title.render("Sudoku", True, BLACK)
            screen.blit(title, (SCREEN_WIDTH//2 - title.get_width()//2, 100))
            for btn in [btn_start, btn_diff, btn_quit]:
                btn.check_hover(mouse_pos)
                btn.draw(screen)

        elif game_state == "GAME":
            # GAME screen
            # Update and draw timer
            elapsed_time = time.time() - start_time
            
            btn_menu.check_hover(mouse_pos)
            btn_menu.draw(screen)
            btn_pencil.check_hover(mouse_pos)
            btn_pencil.draw(screen)
            
            # Timer (top left)
            minutes = int(elapsed_time // 60)
            seconds = int(elapsed_time % 60)
            timer_text = f"Time: {minutes:02d}:{seconds:02d}"
            surf_timer = font_info.render(timer_text, True, DARK_BLUE)
            screen.blit(surf_timer, (20, 60))
            
            # Information in the middle (difficulty, score, mistakes)
            diff_text = difficulty_levels[current_diff_idx]
            score_text = f"Complexity: {current_score}"
            lives_text = f"Mistakes: {3 - lives}/3"
            
            # Color of mistake text (red when only one left)
            lives_color = RED if lives == 1 else DARK_BLUE

            surf_diff = font_info.render(diff_text, True, BLACK)
            surf_score = font_info.render(score_text, True, BLACK)
            surf_lives = font_info.render(lives_text, True, lives_color)
            
            screen.blit(surf_diff, (SCREEN_WIDTH//2 - surf_diff.get_width()//2, 10))
            screen.blit(surf_score, (SCREEN_WIDTH//2 - surf_score.get_width()//2, 35))
            screen.blit(surf_lives, (SCREEN_WIDTH//2 - surf_lives.get_width()//2, 60))

            # Draw Sudoku grid
            draw_sudoku_grid(screen, current_grid, fixed_grid, solution_grid, pencil_grid, selected_cell)
            
        elif game_state == "GAMEOVER":
            # GAME OVER screen (Out of lives)
            txt_over = font_gameover.render("GAME OVER", True, RED)
            txt_msg = font_ui.render("You ran out of lives!", True, BLACK)
            
            screen.blit(txt_over, (SCREEN_WIDTH//2 - txt_over.get_width()//2, 250))
            screen.blit(txt_msg, (SCREEN_WIDTH//2 - txt_msg.get_width()//2, 320))
            
            btn_gameover_menu.check_hover(mouse_pos)
            btn_gameover_menu.draw(screen)
        
        elif game_state == "WIN":
            # WIN screen
            txt_win = font_gameover.render("CONGRATULATIONS!", True, GREEN)
            txt_msg = font_ui.render("You solved the Sudoku!", True, BLACK)
            
            # Show time
            minutes = int(elapsed_time // 60)
            seconds = int(elapsed_time % 60)
            time_text = f"Time: {minutes:02d}:{seconds:02d}"
            txt_time = font_title.render(time_text, True, DARK_BLUE)
            
            # Show number of mistakes
            errors_text = f"Mistakes: {total_errors}"
            txt_errors = font_ui.render(errors_text, True, BLACK)
            
            screen.blit(txt_win, (SCREEN_WIDTH//2 - txt_win.get_width()//2, 200))
            screen.blit(txt_msg, (SCREEN_WIDTH//2 - txt_msg.get_width()//2, 280))
            screen.blit(txt_time, (SCREEN_WIDTH//2 - txt_time.get_width()//2, 340))
            screen.blit(txt_errors, (SCREEN_WIDTH//2 - txt_errors.get_width()//2, 430))
            
            btn_win_menu.check_hover(mouse_pos)
            btn_win_menu.draw(screen)

        # Update display
        pygame.display.flip()
        clock.tick(60)  # 60 FPS

    # Close application
    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
"""
SUDOKU GUI - PYGAME UŽIVATELSKÉ ROZHRANÍ
==========================================
Interaktivní Sudoku hra s pygame knihovnou.
Hráč doplňuje čísla a dostává zpětnou vazbu o správnosti.

Klíčové vlastnosti:
- Grafické zobrazení mřížky
- Pencil marks (poznámky)
- Systém životů (3 chyby = game over)
- Počítadlo času a bodů
- Menu s výběrem obtížnosti

Autor: Leoš Hejlek
Datum: 2026-02-11
"""

import pygame
import sys
import copy
import time

# --- NAČTENÍ LOGIKY (Sudoku modul) ---
try:
    import sudoku
except ImportError:
    print("CHYBA: Soubor 'sudoku.py' nebyl nalezen!")
    sys.exit()

# ============================================================================
# KONFIGURACE HRY
# ============================================================================

# Rozměry okna (v pixelech)
SCREEN_WIDTH = 600      # Šírka okna
SCREEN_HEIGHT = 750     # Výška okna (obsahuje i UI prvky nahoře)
GRID_SIZE = 540         # Velikost mřížky (9x9)
CELL_SIZE = GRID_SIZE // 9  # Velikost jedné buňky (60x60)
MARGIN = (SCREEN_WIDTH - GRID_SIZE) // 2  # Horizontální okraj
START_Y = 80            # Pozice mřížky od horního okraje

# ============================================================================
# BARVY (RGB)
# ============================================================================

WHITE = (255, 255, 255)     # Bílá - pozadí buněk
BLACK = (0, 0, 0)           # Černá - čísla a čáry
GRAY = (200, 200, 200)      # Šedá - tlačítka
BLUE = (50, 150, 255)       # Modrá - primární tlačítka
DARK_BLUE = (0, 100, 200)   # Tmavá modrá - hovor, skóre
RED = (220, 20, 60)         # Červená - error, chyby
GREEN = (34, 139, 34)       # Zelená - "lehké"
ORANGE = (255, 165, 0)      # Oranžová - "těžké"
YELLOW = (255, 215, 0)      # Zlatá - aktivní tlačítko
USER_COLOR = (0, 0, 150)    # Tmavě modrá - správně doplněná čísla
HIGHLIGHT = (255, 255, 200) # Světlá žlutá - zvýraznění vybraného
BG_COLOR = (240, 248, 255)  # Průzračně modrá - pozadí
PENCIL_COLOR = (100, 100, 100)

pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Sudoku")

# Fonty (různé velikosti a styly)
font_nums = pygame.font.SysFont('arial', 40, bold=True)     # Čísla v buňkách
font_pencil = pygame.font.SysFont('arial', 15, bold=True)  # Poznámky (tužka)
font_ui = pygame.font.SysFont('arial', 25)                 # Tlačítka
font_title = pygame.font.SysFont('comicsans', 60)         # Nadpis hry
font_info = pygame.font.SysFont('arial', 20)              # Informace (čas, skóre)
font_gameover = pygame.font.SysFont('arial', 50, bold=True)  # Konec hry

# ============================================================================
# TŘÍDA BUTTON - INTERAKTIVNÍ TLAČÍTKO
# ============================================================================

class Button:
    """
    Reprezentuje interaktivní tlačítko s efekty při najetí myší.
    
    Vlastnosti:
    - text: Popis na tlačítku
    - rect: Pozice a velikost
    - barvy: Základní a barva při najetí
    - aktivní stav: Zvýraznění když je vybráno
    """
    def __init__(self, text, x, y, w, h, color, hover_color):
        """
        Vytvoří nové tlačítko.
        
        Args:
            text: Text na tlačítku
            x, y: Pozice (levý horní roh)
            w, h: Šířka a výška
            color: Základní barva
            hover_color: Barva když je myška nad tlačítkem
        """
        self.text = text
        self.rect = pygame.Rect(x, y, w, h)
        self.base_color = color
        self.hover_color = hover_color
        self.current_color = color
        self.active = False  # Zda je tlačítko aktivní (vybráno)

    def update_text(self, new_text):
        """Změnit text na tlačítku"""
        self.text = new_text

    def update_color(self, new_color, new_hover):
        """Změnit barvy tlačítka"""
        self.base_color = new_color
        self.hover_color = new_hover

    def set_active(self, is_active):
        """
        Nastavit aktivní stav tlačítka.
        Aktivní tlačítko se zvýrazní žlutě.
        """
        self.active = is_active
        if self.active:
            self.current_color = YELLOW
        else:
            self.current_color = self.base_color

    def draw(self, screen):
        """
        Vykreslit tlačítko na obrazovku.
        
        Kreslí:
        1. Stín (tmavý offset)
        2. Hlavní tlačítko
        3. Okraj
        4. Text
        """
        draw_color = YELLOW if self.active else self.current_color
        
        # Stín
        pygame.draw.rect(screen, (50, 50, 50), 
                        (self.rect.x + 2, self.rect.y + 2, self.rect.w, self.rect.h), 
                        border_radius=12)
        # Hlavní tlačítko
        pygame.draw.rect(screen, draw_color, self.rect, border_radius=12)
        # Okraj
        pygame.draw.rect(screen, BLACK, self.rect, 2, border_radius=12)
        
        # Text
        text_color = BLACK if self.active else WHITE
        text_surf = font_ui.render(self.text, True, text_color)
        text_rect = text_surf.get_rect(center=self.rect.center)
        screen.blit(text_surf, text_rect)

    def check_hover(self, mouse_pos):
        """Zkontrolovat jestli je myška nad tlačítkem a změnit barvu"""
        if not self.active:
            self.current_color = self.hover_color if self.rect.collidepoint(mouse_pos) else self.base_color

    def is_clicked(self, mouse_pos):
        """Ověřit jestli bylo na tlačítko kliknuto"""
        return self.rect.collidepoint(mouse_pos)

# ============================================================================
# FUNKCE PRO VYKRESLOVÁNÍ MŘÍŽKY
# ============================================================================

def draw_sudoku_grid(screen, current_grid, fixed_grid, solution_grid, pencil_grid, selected_cell):
    """
    Vykreslí kompletní Sudoku mřížku s obsahem.
    
    KO KRESLÍ:
    1. Pozadí (bílé buňky)
    2. Zvýraznění vybraného políčka
    3. Čísla ve správných barvách
    4. Poznámky (tužka) - malá čísla
    5. Čáry mřížky (tenké mezi buňkami, tlusté mezi boxy)
    6. Vnější ohraničení
    
    Args:
        screen: Pygame surface pro kreslení
        current_grid: Aktuální stav v hře
        fixed_grid: Čísla kterým já uzamčená (zadání + správně doplněná)
        solution_grid: Správné řešení
        pencil_grid: Poznámky v buňkách
        selected_cell: Aktuálně vybrané politčka (r, c) nebo None
    """
    # Vykreslít bílé pozadí mřížky
    pygame.draw.rect(screen, WHITE, (MARGIN, START_Y, GRID_SIZE, GRID_SIZE))
    
    # Zvýraznit vybrané políčko
    if selected_cell:
        r, c = selected_cell
        x = MARGIN + c * CELL_SIZE
        y = START_Y + r * CELL_SIZE
        pygame.draw.rect(screen, HIGHLIGHT, (x, y, CELL_SIZE, CELL_SIZE))

    # === KRESLENÍ OBSAHU BUNĚK ===
    for r in range(9):
        for c in range(9):
            val = current_grid[r][c]
            x_cell = MARGIN + c * CELL_SIZE
            y_cell = START_Y + r * CELL_SIZE

            # A) VELKÉ ČÍSLO (pokud je buňka vyplněna)
            if val != 0:
                # ČERNÉ - bylo zadáno (v fixed_grid)
                # ČERVENÉ - uživatel to zadal špatně
                if fixed_grid[r][c] != 0:
                    color = BLACK  # Zadání nebo správně doplněné
                else:
                    color = RED    # Uživatel zadat špatně

                text = font_nums.render(str(val), True, color)
                x_pos = x_cell + (CELL_SIZE // 2 - text.get_width() // 2)
                y_pos = y_cell + (CELL_SIZE // 2 - text.get_height() // 2) + 2
                screen.blit(text, (x_pos, y_pos))
            
            # B) POZNÁMKY V TUŽCE (malá čísla)
            else:
                marks = pencil_grid[r][c]
                if marks:
                    for mark in marks:
                        # Pozice malého čísla v buňce
                        # Buňka 60x60 je dělena 3x3, takže je 20x20 na číslo
                        row_in_cell = (mark - 1) // 3
                        col_in_cell = (mark - 1) % 3
                        offset_x = col_in_cell * (CELL_SIZE // 3) + (CELL_SIZE // 6)
                        offset_y = row_in_cell * (CELL_SIZE // 3) + (CELL_SIZE // 6)
                        text = font_pencil.render(str(mark), True, PENCIL_COLOR)
                        screen.blit(text, (x_cell + offset_x - text.get_width()//2, 
                                          y_cell + offset_y - text.get_height()//2))

    # === KRESLENÍ MŘÍŽKY (ČÁRY) ===
    for i in range(10):
        # Každá 3. čára (ohraničení boxů) je tlustší
        thickness = 4 if i % 3 == 0 else 1
        color = BLACK if i % 3 == 0 else (160, 160, 160)
        
        # Horizontální čáry
        pygame.draw.line(screen, color, 
                        (MARGIN, START_Y + i * CELL_SIZE), 
                        (MARGIN + GRID_SIZE, START_Y + i * CELL_SIZE), 
                        thickness)
        
        # Vertikální čáry
        pygame.draw.line(screen, color, 
                        (MARGIN + i * CELL_SIZE, START_Y), 
                        (MARGIN + i * CELL_SIZE, START_Y + GRID_SIZE), 
                        thickness)
    
    # Vnější ohraničení (tlusté)
    pygame.draw.rect(screen, BLACK, (MARGIN, START_Y, GRID_SIZE, GRID_SIZE), 4)


# ============================================================================
# HLAVNÍ HERNÍ SMYČKA
# ============================================================================

def main():
    """
    Hlavní herní smyčka. Řídí:
    - Detekci akcí (klávesnicí, myší)
    - Změny stavů (MENU -> GAME -> WIN/GAMEOVER)
    - Herní logiku (validaci tahů, počítané жичích...) 
    - Vykreslování (dle aktuálního stavu)
    """
    clock = pygame.time.Clock()  # Pro FPS
    running = True
    game_state = "MENU"  # Stavy: MENU, GAME, GAMEOVER, WIN
    
    # === HERNÍ DATA ===
    current_grid = None        # Aktuální stav v hře
    fixed_grid = None          # Co je zamčeno
    solution_grid = None       # Správné řešení
    pencil_grid = [[set() for _ in range(9)] for _ in range(9)]  # Poznámky
    
    selected_cell = None       # Vybrané políčka (r, c)
    current_score = 0          # Bodů (obtížnost Sudoku)
    lives = 3                  # Počet živ (max 3 chyby)
    total_errors = 0           # Celkový počet chyb
    
    pencil_mode = False        # Zda je zapnutý režim tužky
    
    # === ČASOVAČ ===
    start_time = 0
    elapsed_time = 0
    
    # === NASTAVENÍ OBTÍŽNOSTI ===
    difficulty_levels = ["Lehké", "Střední", "Těžké"]
    holes_map = [30, 45, 54]  # Počet děr dle obtížnosti
    colors_map = [GREEN, BLUE, ORANGE]  # Barvy dle obtížnosti
    current_diff_idx = 1

    # === TLAČÍTKA ===
    # MENU tlačítka
    btn_start = Button("Start Hry", 150, 250, 300, 60, BLUE, DARK_BLUE)
    btn_diff = Button(f"Obtížnost: {difficulty_levels[current_diff_idx]}", 150, 350, 300, 60, 
                     colors_map[current_diff_idx], (100, 100, 100))
    btn_quit = Button("Konec", 150, 450, 300, 60, RED, (200, 0, 0))
    
    # GAME tlačítka
    btn_menu = Button("Zpět", 20, 10, 80, 40, GRAY, (150, 150, 150))
    btn_pencil = Button("Tužka", 480, 10, 100, 40, GRAY, (180, 180, 180))

    # GAMEOVER a WIN tlačítka
    btn_gameover_menu = Button("Zpět do Menu", 150, 400, 300, 60, BLUE, DARK_BLUE)
    btn_win_menu = Button("Zpět do Menu", 150, 500, 300, 60, BLUE, DARK_BLUE)

    # === HERNÍ SMYČKA ===
    while running:
        mouse_pos = pygame.mouse.get_pos()
        screen.fill(BG_COLOR)

        # === DETEKCE AKCÍ ===
        for event in pygame.event.get():
            # Zavření okna
            if event.type == pygame.QUIT:
                running = False
            
            # === KLIKNUTÍ MYŠÍ ===
            if event.type == pygame.MOUSEBUTTONDOWN:
                # MENU - Kliknutí na tlačítka
                if game_state == "MENU":
                    if btn_start.is_clicked(mouse_pos):
                        # Generuji novou hru
                        screen.fill(BG_COLOR)
                        msg = font_title.render("Generuji...", True, BLACK)
                        screen.blit(msg, (180, 300))
                        pygame.display.flip()
                        
                        # Vygenerovat nové Sudoku se zvolenou obtížností
                        pocet_dier = holes_map[current_diff_idx]
                        grid_zadani, grid_reseni, skore = sudoku.vygeneruj_hru(pocet_dier=pocet_dier)
                        
                        # Inicializace herní gridu
                        current_grid = [row[:] for row in grid_zadani]
                        fixed_grid = [row[:] for row in grid_zadani]  # Co je zamčeno
                        solution_grid = grid_reseni
                        pencil_grid = [[set() for _ in range(9)] for _ in range(9)]
                        
                        # Reset stavů
                        pencil_mode = False
                        btn_pencil.set_active(False)
                        current_score = skore
                        lives = 3
                        total_errors = 0
                        
                        # Spustit časovač
                        start_time = time.time()
                        
                        game_state = "GAME"
                        selected_cell = None
                    
                    elif btn_diff.is_clicked(mouse_pos):
                        # Změnit obtížnost (Lehké -> Střední -> Těžké -> Lehké)
                        current_diff_idx = (current_diff_idx + 1) % 3
                        btn_diff.update_text(f"Obtížnost: {difficulty_levels[current_diff_idx]}")
                        btn_diff.update_color(colors_map[current_diff_idx], (100, 100, 100))

                    elif btn_quit.is_clicked(mouse_pos):
                        running = False

                # GAME - Kliknutí na tlačítka nebo buňky
                elif game_state == "GAME":
                    if btn_menu.is_clicked(mouse_pos):
                        # Zpět do menu
                        game_state = "MENU"
                    elif btn_pencil.is_clicked(mouse_pos):
                        # Přepnout režim tužky
                        pencil_mode = not pencil_mode
                        btn_pencil.set_active(pencil_mode)
                    
                    # Kliknutí na mřížku - vybrat buňku
                    x, y = mouse_pos
                    if MARGIN <= x <= MARGIN + GRID_SIZE and START_Y <= y <= START_Y + GRID_SIZE:
                        col = (x - MARGIN) // CELL_SIZE
                        row = (y - START_Y) // CELL_SIZE
                        selected_cell = (row, col)
                    else:
                        selected_cell = None
                
                # GAMEOVER - Kliknutí na Menu tlačítko
                elif game_state == "GAMEOVER":
                    if btn_gameover_menu.is_clicked(mouse_pos):
                        game_state = "MENU"
                
                # WIN - Kliknutí na Menu tlačítko
                elif game_state == "WIN":
                    if btn_win_menu.is_clicked(mouse_pos):
                        game_state = "MENU"

            # === KLÁVESNICE (POUZE V HERNÍM STAVU) ===
            if event.type == pygame.KEYDOWN and game_state == "GAME":
                if selected_cell:
                    r, c = selected_cell
                    # Zápis povolíme jen pokud pole není zamčeno
                    if fixed_grid[r][c] == 0:
                        
                        key_num = None
                        # Mapování kláves čísel 1-9
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
                                # REŽIM TUŽKY: Přepnout poznámku (bez validace)
                                if key_num in pencil_grid[r][c]:
                                    pencil_grid[r][c].remove(key_num)
                                else:
                                    pencil_grid[r][c].add(key_num)
                            else:
                                # REŽIM PERA: Doplnit číslo a zkontrolovat
                                if key_num == solution_grid[r][c]:
                                    # ✓ SPRÁVNĚ - zamknout políčko
                                    current_grid[r][c] = key_num
                                    fixed_grid[r][c] = key_num  # Zamknutí
                                    pencil_grid[r][c] = set()  # Smazat poznámky
                                    
                                    # Kontrola výhry
                                    if sudoku.je_vyreseno(current_grid):
                                        elapsed_time = time.time() - start_time
                                        game_state = "WIN"
                                else:
                                    # ✗ CHYBA - odečíst život
                                    current_grid[r][c] = key_num
                                    lives -= 1
                                    total_errors += 1
                                    if lives <= 0:
                                        elapsed_time = time.time() - start_time
                                        game_state = "GAMEOVER"

                        # Mazání políčka (Backspace/Delete)
                        if event.key == pygame.K_BACKSPACE or event.key == pygame.K_DELETE:
                            current_grid[r][c] = 0
                            pencil_grid[r][c] = set()

                # Navigace pomocí šipek
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

        # === VYKRESLOVÁNÍ (DLE STAVU) ===
        if game_state == "MENU":
            # MENU obrazovka
            title = font_title.render("Sudoku", True, BLACK)
            screen.blit(title, (SCREEN_WIDTH//2 - title.get_width()//2, 100))
            for btn in [btn_start, btn_diff, btn_quit]:
                btn.check_hover(mouse_pos)
                btn.draw(screen)

        elif game_state == "GAME":
            # HERNÍ obrazovka
            # Aktualizace a kreslení časovače
            elapsed_time = time.time() - start_time
            
            btn_menu.check_hover(mouse_pos)
            btn_menu.draw(screen)
            btn_pencil.check_hover(mouse_pos)
            btn_pencil.draw(screen)
            
            # Časovač (vlevo nahoře)
            minutes = int(elapsed_time // 60)
            seconds = int(elapsed_time % 60)
            timer_text = f"Čas: {minutes:02d}:{seconds:02d}"
            surf_timer = font_info.render(timer_text, True, DARK_BLUE)
            screen.blit(surf_timer, (20, 60))
            
            # Informace uprostřed (obtížnost, skóre, chyby)
            diff_text = difficulty_levels[current_diff_idx]
            score_text = f"Složitost: {current_score}"
            lives_text = f"Chyby: {3 - lives}/3"
            
            # Barva textu chyb (červená když zbývá poslední)
            lives_color = RED if lives == 1 else DARK_BLUE

            surf_diff = font_info.render(diff_text, True, BLACK)
            surf_score = font_info.render(score_text, True, BLACK)
            surf_lives = font_info.render(lives_text, True, lives_color)
            
            screen.blit(surf_diff, (SCREEN_WIDTH//2 - surf_diff.get_width()//2, 10))
            screen.blit(surf_score, (SCREEN_WIDTH//2 - surf_score.get_width()//2, 35))
            screen.blit(surf_lives, (SCREEN_WIDTH//2 - surf_lives.get_width()//2, 60))

            # Kreslení Sudoku mřížky
            draw_sudoku_grid(screen, current_grid, fixed_grid, solution_grid, pencil_grid, selected_cell)
            
        elif game_state == "GAMEOVER":
            # OBRAZOVKA KONCE (Došly životy)
            txt_over = font_gameover.render("GAME OVER", True, RED)
            txt_msg = font_ui.render("Došly ti životy!", True, BLACK)
            
            screen.blit(txt_over, (SCREEN_WIDTH//2 - txt_over.get_width()//2, 250))
            screen.blit(txt_msg, (SCREEN_WIDTH//2 - txt_msg.get_width()//2, 320))
            
            btn_gameover_menu.check_hover(mouse_pos)
            btn_gameover_menu.draw(screen)
        
        elif game_state == "WIN":
            # OBRAZOVKA VÝHRY
            txt_win = font_gameover.render("GRATULUJI!", True, GREEN)
            txt_msg = font_ui.render("Vyřešil jsi sudoku!", True, BLACK)
            
            # Zobrazení času
            minutes = int(elapsed_time // 60)
            seconds = int(elapsed_time % 60)
            time_text = f"Čas: {minutes:02d}:{seconds:02d}"
            txt_time = font_title.render(time_text, True, DARK_BLUE)
            
            # Zobrazení počtu chyb
            errors_text = f"Počet chyb: {total_errors}"
            txt_errors = font_ui.render(errors_text, True, BLACK)
            
            screen.blit(txt_win, (SCREEN_WIDTH//2 - txt_win.get_width()//2, 200))
            screen.blit(txt_msg, (SCREEN_WIDTH//2 - txt_msg.get_width()//2, 280))
            screen.blit(txt_time, (SCREEN_WIDTH//2 - txt_time.get_width()//2, 340))
            screen.blit(txt_errors, (SCREEN_WIDTH//2 - txt_errors.get_width()//2, 430))
            
            btn_win_menu.check_hover(mouse_pos)
            btn_win_menu.draw(screen)

        # Aktualizace displeje
        pygame.display.flip()
        clock.tick(60)  # 60 FPS

    # Zavření aplikace
    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
"""
SUDOKU GENERÁTOR A SOLVER
=========================
Modul pro generování Sudoku hádanek a měření jejich obtížnosti
pomocí simulace řešení konvenčními logickými metodami.
"""

import random
import copy

# ============================================================================
# ČÁST 1: POMOCNÉ FUNKCE PRO VALIDACI
# ==========================================================================

def je_valid(pole, radek, sloupec, cislo):
    """
    Ověří, zda je možné doplnit číslo na dané místo bez porušení Sudoku pravidel.
    """
    # Kontrola řádku - číslo nesmí být v řádku
    if cislo in pole[radek]:
        return False
    
    # Kontrola sloupce - číslo nesmí být ve sloupci
    for r in range(9):
        if pole[r][sloupec] == cislo:
            return False
    
    # Kontrola 3x3 boxu - číslo nesmí být v boxu
    sr, ss = 3 * (radek // 3), 3 * (sloupec // 3)
    for r in range(sr, sr + 3):
        for s in range(ss, ss + 3):
            if pole[r][s] == cislo:
                return False
    
    return True


def spocitej_reseni(pole):
    """
    Spočítá počet možných řešení Sudoku.
    Používá se pro ověření, že vygenerované Sudoku má právě jedno řešení.
    """
    # Najít první prázdné políčko
    empty = None
    for r in range(9):
        for s in range(9):
            if pole[r][s] == 0:
                empty = (r, s)
                break
        if empty:
            break
    
    # Pokud nejsou žádná prázdná políčka, máme jedno řešení
    if not empty:
        return 1
    
    # Zkusit všechna čísla na pozici
    r, s = empty
    count = 0
    for c in range(1, 10):
        if je_valid(pole, r, s, c):
            pole[r][s] = c
            count += spocitej_reseni(pole)
            pole[r][s] = 0  # Zpět
            if count > 1:  # Optimalizace: nemůžeme pokračovat pokud máme více řešení
                return 2
    
    return count


# ============================================================================
# ČÁST 2: GENERÁTOR SUDOKU
# ============================================================================

def doplneni_pole(pole):
    """
    Vyplní prázdné Sudoku pole validním řešením pomocí backtrackingu.
    """
    # Najít první prázdné políčko
    empty = None
    for r in range(9):
        for s in range(9):
            if pole[r][s] == 0:
                empty = (r, s)
                break
        if empty:
            break
    
    # Pokud nemáme prázdná políčka, jsme hotovi
    if not empty:
        return True
    
    # Zkusit čísla v náhodném pořadí (aby vygenerovaná Sudoku byla rozmanitá)
    r, s = empty
    nums = list(range(1, 10))
    random.shuffle(nums)
    
    for c in nums:
        if je_valid(pole, r, s, c):
            pole[r][s] = c
            if doplneni_pole(pole):  # Rekurzivně pokračovat
                return True
            pole[r][s] = 0  # Backtrack
    
    return False


def odeber_cisla(pole, pocet_k_odebrani):
    """
    Odebere čísla z vyplněného Sudoku, ale hlídá aby zůstalo právě jedno řešení."""
    # Vytvořit seznam všech souřadnic a zamíchat je
    coords = [(r, s) for r in range(9) for s in range(9)]
    random.shuffle(coords)
    
    odebrano = 0
    # Procházet souřadnice a odebírat čísla
    for r, s in coords:
        if odebrano >= pocet_k_odebrani:
            break
        
        # Uložit původní hodnotu
        zaloha = pole[r][s]
        pole[r][s] = 0
        
        # Ověřit že Sudoku má stále právě jedno řešení
        kopie = [row[:] for row in pole]
        if spocitej_reseni(kopie) != 1:
            # Vrátit číslici zpět pokud by vzniklo více řešení
            pole[r][s] = zaloha
        else:
            odebrano += 1
    
    return pole


def je_vyreseno(grid):
    """
    Ověří, zda je Sudoku správně a kompletně vyřešeno
    """
    # Kontrola rozměrů
    if not grid or len(grid) != 9 or not all(isinstance(row, list) and len(row) == 9 for row in grid):
        return False

    # Správná sada čísel (1-9)
    referenci_mnozina = set(range(1, 10))

    # Kontrola řádků a sloupců
    for i in range(9):
        # Řádek
        if set(grid[i]) != referenci_mnozina:
            return False
        
        # Sloupec
        sloupec = [grid[j][i] for j in range(9)]
        if set(sloupec) != referenci_mnozina:
            return False

    # Kontrola 3x3 boxů
    for i in range(0, 9, 3):
        for j in range(0, 9, 3):
            blok = [
                grid[x][y]
                for x in range(i, i + 3)
                for y in range(j, j + 3)
            ]
            if set(blok) != referenci_mnozina:
                return False

    return True


# ============================================================================
# ČÁST 3: URČOVÁNÍ OBTÍŽNOSTI - METODY ŘEŠENÍ
# ============================================================================

def urceni_slozitosti(vstupni_pole):
    """
    Měří obtížnost Sudoku simulací řešení konvenčními logickými metodami.
    
    ALGORITMUS:
    ===========
    1. Nejdřív zkoušíme jednoduché metody (bez mapování kandidátů)
    2. Pokud nestačí, aktivujeme systém kandidátů
    3. Pak zkoušíme pokročilé metody
    4. Na konci vrátíme skóre a indikátor řešitelnosti
    
    BODOVÁNÍ:
    =========
    - Poslední volné: 1 bod
    - Jediná možnost: 2 body
    - Jediné umístění: 3 body
    - Směřující dvojice: 6 bodů
    - Viditelné dvojice: 4-5 bodů
    - Skryté dvojice: 10 bodů
    - Viditelné trojice: 15 bodů
    - X-křídlo: 25 bodů
    """
    pole = [r[:] for r in vstupni_pole]  # Kopie aby jsme neponičili vstup
    skore = 0
    
    # Kandidáti = možná čísla pro každé políčko
    # Inicializace prázdných sad (povolujeme až po aktivaci)
    kandidati = [[set() for _ in range(9)] for _ in range(9)]
    kandidati_aktivni = False

    def refresh_kandidaty():
        """Přepočítá všechny kandidáty na základě aktuálního stavu pole"""
        for r in range(9):
            for s in range(9):
                if pole[r][s] == 0:
                    cands = set()
                    for c in range(1, 10):
                        if je_valid(pole, r, s, c):
                            cands.add(c)
                    kandidati[r][s] = cands
                else:
                    kandidati[r][s] = set()

    def update_po_tahu(r, s, c):
        """
        Aktualizuje kandidáty po doplnění čísla.
        Vymaže kandidáta c z všech políček v řádku, sloupci a boxu.
        """
        if not kandidati_aktivni:
            return
        # Vymazat c z řádku
        for i in range(9):
            kandidati[r][i].discard(c)
        # Vymazat c ze sloupce
        for i in range(9):
            kandidati[i][s].discard(c)
        # Vymazat c z boxu
        sr, ss = (r // 3) * 3, (s // 3) * 3
        for i in range(sr, sr + 3):
            for j in range(ss, ss + 3):
                kandidati[i][j].discard(c)
        kandidati[r][s] = set()

    # ========================================================================
    # JEDNODUCHÉ METODY (BEZ KANDIDÁTŮ) - FÁZE 1
    # ========================================================================

    def m_poslední_volné():
        """
        POSLEDNÍ VOLNÉ (Full House / Poslední v jednotce)
        
        VYSVĚTLENÍ:
        Pokud v řádku, sloupci nebo boxu zbývá jen jedna nula,
        víme přesně jaké číslo tam patří. Je to číslo, které vté 
        jednotce chybí.
        
        PŘÍKLAD:
        Řádek: [1, 2, 3, 4, 5, 6, 7, 8, _]
        Chybí: 9
        
        BODŮ: 1 bod za každou nalezenou hodnotu
        """
        change = False
        pts = 0
        units = []
        
        # Vytvořit seznamy jednotek (řádky, sloupce, boxy)
        # Řádky
        for i in range(9):
            units.append([(i, j) for j in range(9)])
        # Sloupce
        for i in range(9):
            units.append([(j, i) for j in range(9)])
        # Boxy (3x3)
        for i in range(9):
            sr, ss = (i // 3) * 3, (i % 3) * 3
            units.append([(r, s) for r in range(sr, sr + 3) for s in range(ss, ss + 3)])

        # Procházet všechny jednotky
        for unit in units:
            vals = [pole[r][s] for r, s in unit]
            # Pokud je jen jedna nula v jednotce
            if vals.count(0) == 1:
                # Najít chybějící číslo (to které není v jednotce)
                missing = [n for n in range(1, 10) if n not in vals][0]
                # Najít pozici nuly a doplnit ji
                for r, s in unit:
                    if pole[r][s] == 0:
                        pole[r][s] = missing
                        update_po_tahu(r, s, missing)
                        change = True
                        pts += 1
                        break
        return change, pts

    def m_jediná_možnost():
        """
        JEDINÁ MOŽNOST (Naked Single / Nudé jedináče)
        
        VYSVĚTLENÍ:
        Pokud má políčko jen jednu platnou možnost (jen jedno číslo 
        které se tam dá doplnit bez konfliktu), tak víme co tam patří.
        BODŮ: 2 body za každou nalezenou hodnotu
        """
        change = False
        pts = 0
        for r in range(9):
            for s in range(9):
                if pole[r][s] == 0:
                    # Najít všechny platné kandidáty
                    mozne = [c for c in range(1, 10) if je_valid(pole, r, s, c)]
                    # Pokud je jen jeden, můžeme ho doplnit
                    if len(mozne) == 1:
                        val = mozne[0]
                        pole[r][s] = val
                        update_po_tahu(r, s, val)
                        change = True
                        pts += 2
        return change, pts

    def m_jediné_umístění():
        """
        JEDINÉ UMÍSTĚNÍ (Hidden Single / Skryté jedináče)
        
        VYSVĚTLENÍ:
        Pokud se číslo v řádku/sloupci vyskytuje jen v jednom místě,
        víme kde musí být. Například pokud se 5 v řádku vyskytuje
        jen v jedné prázdné buňce, tak tam musí být.
        
        PŘÍKLAD:
        Řádek: [_, _, _, 5, _, _, _, _, _]
        Hledáme kde se dá doplnit 5
        - Políčko 1: se dá
        - Políčko 2: nelze (konflikt se sloupcem)
        - Políčko 3: nelze (konflikt s boxem)
        - itd.
        Jen jedno místo -> doplníme tam
        
        BODŮ: 3 body za každou nalezenou hodnotu
        """
        change = False
        pts = 0
        for c in range(1, 10):
            # Kontrola řádků
            for r in range(9):
                if c not in pole[r]:  # Pokud c už není v řádku
                    places = []
                    for s in range(9):
                        # Kde se dá doplnit c
                        if pole[r][s] == 0 and je_valid(pole, r, s, c):
                            places.append((r, s))
                    # Pokud je jen jedno místo, doplníme
                    if len(places) == 1:
                        rr, ss = places[0]
                        pole[rr][ss] = c
                        update_po_tahu(rr, ss, c)
                        change = True
                        pts += 3
            
            # Kontrola sloupců
            for s in range(9):
                if c not in [pole[r][s] for r in range(9)]:  # Pokud c není ve sloupci
                    places = []
                    for r in range(9):
                        # Kde se dá doplnit c
                        if pole[r][s] == 0 and je_valid(pole, r, s, c):
                            places.append((r, s))
                    # Pokud je jen jedno místo, doplníme
                    if len(places) == 1:
                        rr, ss = places[0]
                        pole[rr][ss] = c
                        update_po_tahu(rr, ss, c)
                        change = True
                        pts += 3
        return change, pts

    # ========================================================================
    # POKROČILÉ METODY (VYŽADUJÍ KANDIDÁTY) - FÁZE 2
    # ========================================================================

    def m_viditelne_dvojice():
        """
        VIDITELNÉ DVOJICE (Naked Pairs)
        
        VYSVĚTLENÍ:
        Pokud dvě políčka ve skupině (řádek, sloupec, box) 
        mají identicky STEJNÉ DVA kandidáty, pak tyto dva kandidáti
        nemohou být nikde jinde v té skupině.
        
        PŘÍKLAD:
        Řádek: [..., (3,7), ..., (3,7), ..., (2,3), ...]
                    ↑           ↑          ↑
                  políčko 3   políčko 8   políčko 9
        
        Politčka 3 a 8 mají pouze {3, 7}
        -> 3 a 7 nemohou být v políčku 9 (i když tam mohou být jako kandidáti)
        -> Vyloučíme je z políčka 9
        
        BODŮ: 4-5 bodů za eliminaci (4 pro řádky/sloupce, 5 pro boxy)
        """
        change = False
        pts = 0
        
        # Řádky
        for r in range(9):
            # Najít všechna políčka se dvěma kandidáty
            pairs = [(s, kandidati[r][s]) for s in range(9) if len(kandidati[r][s]) == 2]
            # Porovnat všechny páry
            for i in range(len(pairs)):
                for j in range(i + 1, len(pairs)):
                    s1, k1 = pairs[i]
                    s2, k2 = pairs[j]
                    # Pokud mají stejné kandidáty
                    if k1 == k2:
                        # Vyndat je z ostatních políček v řádku
                        for s in range(9):
                            if s != s1 and s != s2 and not kandidati[r][s].isdisjoint(k1):
                                kandidati[r][s] -= k1
                                change = True
                                pts += 4
        
        # Sloupce
        for s in range(9):
            pairs = [(r, kandidati[r][s]) for r in range(9) if len(kandidati[r][s]) == 2]
            for i in range(len(pairs)):
                for j in range(i + 1, len(pairs)):
                    r1, k1 = pairs[i]
                    r2, k2 = pairs[j]
                    if k1 == k2:
                        for r in range(9):
                            if r != r1 and r != r2 and not kandidati[r][s].isdisjoint(k1):
                                kandidati[r][s] -= k1
                                change = True
                                pts += 4
        
        # Boxy
        for bn in range(9):
            sr, ss = (bn // 3) * 3, (bn % 3) * 3
            cells = []
            for r in range(sr, sr + 3):
                for s in range(ss, ss + 3):
                    if len(kandidati[r][s]) == 2:
                        cells.append((r, s, kandidati[r][s]))
            for i in range(len(cells)):
                for j in range(i + 1, len(cells)):
                    r1, s1, k1 = cells[i]
                    r2, s2, k2 = cells[j]
                    if k1 == k2:
                        for r in range(sr, sr + 3):
                            for s in range(ss, ss + 3):
                                if (r, s) != (r1, s1) and (r, s) != (r2, s2):
                                    if not kandidati[r][s].isdisjoint(k1):
                                        kandidati[r][s] -= k1
                                        change = True
                                        pts += 5
        return change, pts

    def m_smerujici_dvojice():
        """
        SMĚŘUJÍCÍ DVOJICE (Pointing Pairs)
        
        VYSVĚTLENÍ:
        Pokud se kandidát v boxu vyskytuje jen v jednom řádku či sloupci,
        pak se nemůže vyskytovat v ostatních boxech v tom řádku/sloupci.
        
        PŘÍKLAD:
        Box (levý horní):
        [1, _, _]
        [_, _, 5]
        [_, _, 2]
        
        Jako kandidáti jsou: {1}, {3,4}, {6,7}, ...
        Řekněme že 8 se v boxu vyskytuje jen v prvním řádku:
        [1, _, 8]  (jen zde)
        [_, _, _]
        [_, _, _]
        
        -> 8 se nemůže vyskytovat v ostatních boxech v prvním řádku
        
        BODŮ: 6 bodů za eliminaci
        """
        change = False
        pts = 0
        for bn in range(9):
            sr, ss = (bn // 3) * 3, (bn % 3) * 3
            for val in range(1, 10):
                # Najít všechny pozice kde se vyskytuje val v tomto boxu
                coords = [
                    (r, s) for r in range(sr, sr + 3) for s in range(ss, ss + 3)
                    if val in kandidati[r][s]
                ]
                if 2 <= len(coords) <= 3:
                    # Všechny jsou v jednom řádku?
                    if all(c[0] == coords[0][0] for c in coords):
                        row = coords[0][0]
                        # Vyloučit z ostatních boxů v tomto řádku
                        for s in range(9):
                            if not (ss <= s < ss + 3) and val in kandidati[row][s]:
                                kandidati[row][s].discard(val)
                                change = True
                                pts += 6
                    # Všechny jsou v jednom sloupci?
                    elif all(c[1] == coords[0][1] for c in coords):
                        col = coords[0][1]
                        # Vyloučit z ostatních boxů v tomto sloupci
                        for r in range(9):
                            if not (sr <= r < sr + 3) and val in kandidati[r][col]:
                                kandidati[r][col].discard(val)
                                change = True
                                pts += 6
        return change, pts

    def m_skryte_dvojice():
        """
        SKRYTÉ DVOJICE (Hidden Pairs)
        
        VYSVĚTLENÍ:
        Pokud se dva kandidáti v řádku vyskytují POUZE ve dvou políčích
        (skrytě, protože tam mohou být i jiní kandidáti), pak mohou být
        v těchto dvou políčkách jen tyto dva kandidáti.
        
        PŘÍKLAD:
        Řádek: [1, {2,3,5}, {2,5}, {4}, {6}, {3,7}, ...]
                        ↑        ↑
        2 se vyskytuje jen v políčcích 2 a 3
        5 se vyskytuje jen v políčcích 2 a 3
        -> V těchto dvou políčkách mohou být jen 2 a 5
        -> Vyloučit 3 a 7 z politčka 2
        
        BODŮ: 10 bodů za eliminaci
        """
        change = False
        pts = 0
        for r in range(9):
            # Zkusit všechny páry kandidátů
            for v1 in range(1, 10):
                for v2 in range(v1 + 1, 10):
                    # Najít místa kde se vyskytují OBA kandidáti
                    pos = [s for s in range(9) if v1 in kandidati[r][s] and v2 in kandidati[r][s]]
                    if len(pos) == 2:
                        # Ověřit že oba kandidáti se vyskytují POUZE v těchto místech
                        v1_count = sum(1 for s in range(9) if v1 in kandidati[r][s])
                        v2_count = sum(1 for s in range(9) if v2 in kandidati[r][s])
                        if v1_count == 2 and v2_count == 2:
                            # Zachovat jen tyto dva kandidáty v těchto políčkách
                            for s in pos:
                                if len(kandidati[r][s]) > 2:
                                    kandidati[r][s] = {v1, v2}
                                    change = True
                                    pts += 10
        return change, pts

    def m_viditelne_trojice():
        """
        VIDITELNÉ TROJICE (Naked Triples)
        
        VYSVĚTLENÍ:
        Pokud tři políčka mají STEJNÉ TŘI kandidáty, pak tyto
        tři kandidáti nemohou být v žádném jiném políčku v té skupině.
        
        (Rozšíření viditelných dvojic)
        
        PŘÍKLAD:
        Řádek: [{2,3,5}, {2,3,5}, {2,3,5}, {1,4,6}, ...]
                   ↑         ↑         ↑
        Tři politčka mají {2,3,5}
        -> 2, 3 a 5 nemohou být nikde jinde v řádku
        -> Vyloučit z politčka {1,4,6}
        
        BODŮ: 15 bodů za eliminaci
        """
        change = False
        pts = 0
        for r in range(9):
            # Najít politčka se 2-3 kandidáty
            cells = [(s, kandidati[r][s]) for s in range(9) if 1 < len(kandidati[r][s]) <= 3]
            if len(cells) < 3:  # Nutně potřebujeme alespoň 3 políčka
                continue
            # Porovnat všechny trojice
            for i in range(len(cells)):
                for j in range(i + 1, len(cells)):
                    for k in range(j + 1, len(cells)):
                        s1, k1 = cells[i]
                        s2, k2 = cells[j]
                        s3, k3 = cells[k]
                        union = k1 | k2 | k3  # Sjednocení všech tří
                        # Pokud je sjednocení právě 3 kandidáty
                        if len(union) == 3:
                            # Vyloučit tyto tři z ostatních políček
                            for s in range(9):
                                if s not in (s1, s2, s3) and not kandidati[r][s].isdisjoint(union):
                                    kandidati[r][s] -= union
                                    change = True
                                    pts += 15
        return change, pts

    def m_x_kridlo():
        """
        X-KŘÍDLO (X-Wing)
        
        VYSVĚTLENÍ:
        Pokročilá metoda. Pokud se kandidát ve dvou řádcích
        vyskytuje jen ve stejných dvou sloupcích, pak se nemůže
        vyskytovat v dalších řádcích v těchto sloupcích.
        
        PŘÍKLAD:
        Řádek 1: ... {1,3} ... {1,5} ...
        Řádek 5: ... {1,2} ... {1,7} ...
        Sloupce: 3, 7
        
        1 se v řádku 1 vyskytuje jen ve sloupcích 3 a 7
        1 se v řádku 5 vyskytuje jen ve sloupcích 3 a 7
        
        Tvar X-křídla:
        Řádek 1, sloupec 3: 1 ❌
        Řádek 1, sloupec 7: 1 ❌
        Řádek 5, sloupec 3: 1 ❌
        Řádek 5, sloupec 7: 1 ❌
        
        -> 1 se nemůže vyskytovat v ostatních řádcích ve sloupcích 3 a 7
        
        BODŮ: 25 bodů za eliminaci
        """
        change = False
        pts = 0
        for val in range(1, 10):
            rows = []
            # Najít řádky kde se val vyskytuje jen ve dvou sloupcích
            for r in range(9):
                cols = [s for s in range(9) if val in kandidati[r][s]]
                if len(cols) == 2:
                    rows.append((r, cols))
            # Najít dva řádky se stejnými sloupci
            for i in range(len(rows)):
                for j in range(i + 1, len(rows)):
                    r1, c1 = rows[i]
                    r2, c2 = rows[j]
                    if c1 == c2:
                        # Vyloučit val z ostatních řádků v těchto sloupcích
                        for r_idx in range(9):
                            if r_idx != r1 and r_idx != r2:
                                for s_idx in c1:
                                    if val in kandidati[r_idx][s_idx]:
                                        kandidati[r_idx][s_idx].discard(val)
                                        change = True
                                        pts += 25
        return change, pts

    # ========================================================================
    # HLAVNÍ SMYČKA ŘEŠENÍ
    # ========================================================================
    limit_kroku = 100

    for _ in range(limit_kroku):
        # ===== FÁZE 1: JEDNODUCHÉ METODY (BEZ KANDIDÁTŮ) =====
        # Zkušujeme jednoduché metody dokud pracují
        
        ok, b = m_poslední_volné()
        if ok:
            skore += b
            continue

        ok, b = m_jediná_možnost()
        if ok:
            skore += b
            continue

        ok, b = m_jediné_umístění()
        if ok:
            skore += b
            continue

        # ===== FÁZE 2: POKROČILÉ METODY (S KANDIDÁTY) =====
        # Pokud jednoduché metody nefungovaly, aktivujeme kandidáty
        if not kandidati_aktivni:
            refresh_kandidaty()
            kandidati_aktivni = True

        # Spustit VŠECHNY pokročilé metody a sbírat jejich body
        zmena_celkove = False
        
        ok, b = m_smerujici_dvojice()
        if ok:
            skore += b
            zmena_celkove = True

        ok, b = m_viditelne_dvojice()
        if ok:
            skore += b
            zmena_celkove = True

        ok, b = m_skryte_dvojice()
        if ok:
            skore += b
            zmena_celkove = True

        ok, b = m_viditelne_trojice()
        if ok:
            skore += b
            zmena_celkove = True

        ok, b = m_x_kridlo()
        if ok:
            skore += b
            zmena_celkove = True

        # Pokud NĚKTERÁ metoda něco udělala, pokračuj znovu (zkus dál jednoduché)
        if zmena_celkove:
            continue

        # Žádná metoda nezabrala -> konec logického řešení
        break

    # --- VYHODNOCENÍ ---
    pocet_prazdnych = sum(row.count(0) for row in pole)

    if pocet_prazdnych == 0:
        # Vyřešeno logicky - vrátit skóre a značku řešitelnosti
        return (skore, True)
    else:
        # Nevyřešeno logicky -> Sudoku vyžaduje hádání (Trial & Error)
        # Vrátit penalizované skóre a značku že není logicky řešitelné
        penalized_score = skore + 50 + (pocet_prazdnych * 5)
        return (penalized_score, False)


# ============================================================================
# ČÁST 4: GENERÁTOR HER
# ============================================================================

def vygeneruj_hru(pocet_dier=40):
    """
    Vygeneruje Sudoku puzzle, které je:
    1. Správně řešitelné (právě jedno řešení)
    2. Logicky řešitelné (bez náhodného hádání)
    3. Dostatečně obtížné (alespoň min_skore bodů)
    
    Pokud Sudoku není logicky řešitelné, vygeneruje nové.
    
    PROCES:
    =======
    1. Vytvořit nové náhodné kompletní Sudoku
    2. Odebrat z něj zadaný počet čísel
    3. Změřit jeho obtížnost
    4. Ověřit že je logicky řešitelné a dostatečně těžké
    5. Pokud ne, zkusit znovu (max 50x)
    
    Args:
        pocet_dier (int): Počet políček k odebrání
                         30=lehké, 45=střední, 54=těžké
    
    Returns:
        tuple: (zadani, reseni, skore)
               - zadani: Sudoku puzzle (s nulami jako prázdná politčka)
               - reseni: Kompletně vyplněné správné řešení
               - skore: Změřená obtížnost (počet bodů)
    """
    
    # --- NASTAVENÍ POŽADAVKŮ PODLE OBTÍŽNOSTI ---
    # Adaptivní systém: čím více děr, tím vyšší skóre požadujeme
    if pocet_dier < 20:
        min_skore = max(1, pocet_dier // 3)  # Max 6 bodů
    elif pocet_dier < 35:
        min_skore = pocet_dier // 2  # Cca 15-17 bodů
    elif pocet_dier < 50:
        min_skore = pocet_dier // 2 + 5  # Cca 22-30 bodů
    else:
        min_skore = 100  # Těžké: alespoň 100 bodů
    
    print(f"Hledám sudoku s {pocet_dier} děrami a min. skóre {min_skore}...")
    
    attempt = 0
    while attempt < 50:  # Max 50 pokusů (abychom neujeli do nekonečna)
        attempt += 1
        
        # --- KROK 1: Vytvořit plné Sudoku ---
        pole = [[0] * 9 for _ in range(9)]
        doplneni_pole(pole)
        plne_reseni = [r[:] for r in pole]
        
        # --- KROK 2: Odebrat čísla a vytvořit puzzle ---
        zadani = odeber_cisla([r[:] for r in pole], pocet_dier)
        
        # --- KROK 3: Měřit obtížnost a ověřit řešitelnost ---
        skore, je_resitelne = urceni_slozitosti(zadani)
        
        # --- KROK 4: Kontrola kritérií ---
        if je_resitelne and skore >= min_skore:
            # Úspěch!
            print(f"Našel jsem! Pokus č. {attempt}, Skóre: {skore}")
            return zadani, plne_reseni, skore
        elif not je_resitelne:
            # Sudoku není logicky řešitelné - zkusit znovu
            print(f"Pokus {attempt}: Sudoku není logicky řešitelné. Zkouším znovu...")

    # Pokud se nepodařilo najít vhodné Sudoku v limitu
    print("Varování: Nepodařilo se najít dostatečně těžké sudoku v limitu. Vracím poslední nalezené.")
    return zadani, plne_reseni, skore

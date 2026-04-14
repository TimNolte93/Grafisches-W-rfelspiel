import pygame
import sys
import random
import json
import os
from datetime import datetime

# --- 1. SETUP ---
pygame.init()
SCREEN_WIDTH, SCREEN_HEIGHT = 1280, 720
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("BlueMarlin-Würfelspiel")
clock = pygame.time.Clock()

# --- FARBEN & SCHRIFTEN ---
WHITE = (255, 255, 255); BLACK = (0, 0, 0)
CASINO_RED = (180, 0, 0); PLAYER_RED = (180, 40, 40)
BRIGHT_RED = (255, 0, 0); GRAY = (50, 50, 50); GOLD = (255, 215, 0)

font_large = pygame.font.SysFont("Arial", 50, bold=True)
font_xl    = pygame.font.SysFont("Arial", 80, bold=True)
font_medium = pygame.font.SysFont("Arial", 32, bold=True)
font_small = pygame.font.SysFont("Arial", 28, bold=True)
font_hint = pygame.font.SysFont("Arial", 26, bold=True)

# --- 2. ASSETS LADEN ---
def load_img(name, size):
    try:
        img = pygame.image.load(f"assets/{name}").convert_alpha()
        return pygame.transform.scale(img, size)
    except:
        surf = pygame.Surface(size); surf.fill((255, 0, 0)); return surf

tisch = load_img("pokertisch.png", (SCREEN_WIDTH, SCREEN_HEIGHT))
menu_bg = load_img("start_bild.png", (SCREEN_WIDTH, SCREEN_HEIGHT))
wuerfel_bilder = [load_img(f"wuerfel_{i}.png", (80, 80)) for i in range(1, 7)]
becher_stehend = load_img("becher_stehend_2.0.png", (200, 250))
becher_schief = load_img("becher_schütteln_2.0.png", (200, 250))
becher_offen = load_img("becher_umgekehrt_2.0.png", (200, 250))
img_pokal = load_img("pokal.png", (200, 200))

img_player_unten = load_img("player_unten.png", (120, 120))
img_player_oben = load_img("player_oben.png", (120, 120))
img_player_rechts = load_img("player_rechts.png", (120, 120))
img_player_links = load_img("player_links.png", (120, 120))

# --- 3. VARIABLEN & ZUSTÄNDE ---
PHASE_MENU = "MENU"; PHASE_MODE_SELECT = "MODE_SELECT"; PHASE_NAME_INPUT = "NAME_INPUT"
PHASE_ROUND_INPUT = "ROUND_INPUT"; PHASE_START = "START"; PHASE_SHAKING = "SHAKING"
PHASE_REVEAL = "REVEAL"; PHASE_FINAL = "FINAL"; PHASE_GAME_OVER = "GAME_OVER"
PHASE_OPTIONS = "OPTIONS"; PHASE_LOAD = "LOAD"; PHASE_HOWTO = "HOWTO"
PHASE_SAVE_NAME = "SAVE_NAME"; PHASE_LEADERBOARD = "LEADERBOARD"

current_phase = PHASE_MENU
phase_vor_dem_speichern = PHASE_START 
game_mode = ""; player_count = 1; player_names = []; player_scores = []
current_player_index = 0; round_counter = 1; max_rounds = 0; active_text = ""; timer = 0
leaderboard_updated = False

wuerfel_ergebnisse = [1] * 5
kept_dice = [False] * 5 
rolls_left = 3          
points_already_added = False 
bonus_msg = ""; bonus_display_timer = 0
save_name_text = ""

# Rects für Buttons
start_button_rect   = pygame.Rect(510, 503, 260, 50)
options_button_rect = pygame.Rect(510, 560, 260, 50)
quit_button_rect    = pygame.Rect(510, 620, 260, 50)

opt_back_rect        = pygame.Rect(50, 620, 200, 50)
opt_load_rect        = pygame.Rect(SCREEN_WIDTH//2 - 150, 230, 300, 50)
opt_leaderboard_rect = pygame.Rect(SCREEN_WIDTH//2 - 150, 300, 300, 50)
opt_howto_rect       = pygame.Rect(SCREEN_WIDTH//2 - 150, 370, 300, 50)

POSITIONS = {
    "unten": (SCREEN_WIDTH // 2 - 180, SCREEN_HEIGHT - 140), 
    "oben": (SCREEN_WIDTH // 2 - 60, 20),
    "links":  (150, SCREEN_HEIGHT // 2 - 60),
    "rechts": (SCREEN_WIDTH - 270, SCREEN_HEIGHT // 2 - 60),
    "becher": (540, 220),
    "wuerfel_y_center": 330,   
    "wuerfel_y_hold": 520,     
    "hint_y_top": SCREEN_HEIGHT - 90,
    "hint_y_bottom": SCREEN_HEIGHT - 50
}
W_START_X = 420; W_HOLD_X = 820   

# --- 4. FUNKTIONEN (SPEICHERN, LADEN, BUBBLE SORT) ---

def update_leaderboard(name, score):
    lb_file = "leaderboard.json"
    data = []
    if os.path.exists(lb_file):
        with open(lb_file, "r") as f: data = json.load(f)
    
    data.append({"name": name, "score": score})
    
    # BUBBLE SORT (Absteigend)
    n = len(data)
    for i in range(n):
        for j in range(0, n - i - 1):
            if data[j]["score"] < data[j + 1]["score"]:
                data[j], data[j + 1] = data[j + 1], data[j]
    
    # Behalte nur Top 5
    data = data[:5]
    with open(lb_file, "w") as f: json.dump(data, f)

def berechne_wertung(wuerfel):
    if not wuerfel: return 0, ""
    counts = [wuerfel.count(i) for i in range(1, 7)]
    unique_sorted = sorted(list(set(wuerfel)))
    if 5 in counts: return 100, "5er Pasch - 100 Punkte"
    if 4 in counts: return 50, "4er Pasch - 50 Punkte"
    if len(unique_sorted) == 5 and (unique_sorted[-1] - unique_sorted[0] == 4): return 75, "Große Straße - 75 Punkte"
    if 3 in counts and 2 in counts: return 50, "Full House - 50 Punkte"
    if 3 in counts: return 25, "3er Pasch - 25 Punkte"
    straights = [[1,2,3,4], [2,3,4,5], [3,4,5,6]]
    for s in straights:
        if all(val in unique_sorted for val in s): return 30, "Kleine Straße - 30 Punkte"
    return 0, ""

def get_save_files():
    if not os.path.exists("saves"): os.makedirs("saves")
    files = [f for f in os.listdir("saves") if f.endswith(".json")]
    return sorted(files, key=lambda x: os.path.getmtime(os.path.join("saves", x)), reverse=True)

def save_game(custom_name, return_phase):
    saves = get_save_files()
    if len(saves) >= 5: os.remove(os.path.join("saves", saves[-1]))
    data = {
        "player_names": player_names, "player_scores": player_scores, "current_player": current_player_index,
        "round": round_counter, "max_rounds": max_rounds, "mode": game_mode, "count": player_count,
        "rolls_left": rolls_left, "kept_dice": kept_dice, "ergebnisse": wuerfel_ergebnisse,
        "points_added": points_already_added, "saved_phase": return_phase, "display_name": custom_name
    }
    filename = f"saves/save_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(filename, "w") as f: json.dump(data, f)

# --- 5. HAUPTSCHLEIFE ---
running = True
while running:
    mouse_pos = pygame.mouse.get_pos()
    off_x, off_y = 0, 0
    aktiver_becher = becher_stehend

    def get_dice_pos(idx):
        if rolls_left == 0 and current_phase == PHASE_FINAL:
            return (W_START_X + (idx * 90), POSITIONS["wuerfel_y_center"])
        if kept_dice[idx]:
            return (W_HOLD_X + (idx * 85), POSITIONS["wuerfel_y_hold"])
        return (W_START_X + (idx * 90), POSITIONS["wuerfel_y_center"])
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            os._exit(0)
        
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            current_phase = PHASE_MENU; active_text = ""; save_name_text = ""

        if current_phase == PHASE_MENU:
            leaderboard_updated = False
            if event.type == pygame.MOUSEBUTTONDOWN:
                if start_button_rect.collidepoint(event.pos): current_phase = PHASE_MODE_SELECT
                elif options_button_rect.collidepoint(event.pos): current_phase = PHASE_OPTIONS
                elif quit_button_rect.collidepoint(event.pos): 
                    pygame.quit()
                    os._exit(0)

        elif current_phase == PHASE_OPTIONS:
            if event.type == pygame.MOUSEBUTTONDOWN:
                if opt_back_rect.collidepoint(event.pos): current_phase = PHASE_MENU
                elif opt_load_rect.collidepoint(event.pos): current_phase = PHASE_LOAD
                elif opt_leaderboard_rect.collidepoint(event.pos): current_phase = PHASE_LEADERBOARD
                elif opt_howto_rect.collidepoint(event.pos): current_phase = PHASE_HOWTO

        elif current_phase == PHASE_SAVE_NAME:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN and save_name_text.strip() != "":
                    save_game(save_name_text, phase_vor_dem_speichern)
                    current_phase = phase_vor_dem_speichern; save_name_text = ""
                elif event.key == pygame.K_BACKSPACE: save_name_text = save_name_text[:-1]
                else: save_name_text += event.unicode if len(save_name_text) < 15 else ""

        elif current_phase == PHASE_LOAD:
            if event.type == pygame.MOUSEBUTTONDOWN:
                if opt_back_rect.collidepoint(event.pos): current_phase = PHASE_OPTIONS
                saves = get_save_files()
                for i, s in enumerate(saves):
                    r = pygame.Rect(SCREEN_WIDTH//2 - 200, 150 + i*70, 400, 50)
                    if r.collidepoint(event.pos):
                        with open(f"saves/{s}", "r") as f:
                            d = json.load(f)
                            player_names, player_scores = d["player_names"], d["player_scores"]
                            current_player_index, round_counter = d["current_player"], d["round"]
                            max_rounds, game_mode, player_count = d["max_rounds"], d["mode"], d["count"]
                            rolls_left, kept_dice, wuerfel_ergebnisse = d["rolls_left"], d["kept_dice"], d["ergebnisse"]
                            points_already_added, current_phase = d["points_added"], d["saved_phase"]

        elif current_phase == PHASE_LEADERBOARD or current_phase == PHASE_HOWTO:
            if event.type == pygame.MOUSEBUTTONDOWN and opt_back_rect.collidepoint(event.pos):
                current_phase = PHASE_OPTIONS

        elif current_phase == PHASE_MODE_SELECT:
            if event.type == pygame.MOUSEBUTTONDOWN:
                rects = [pygame.Rect(SCREEN_WIDTH//2 - 150, 160 + i*70, 300, 50) for i in range(5)]
                for i, r in enumerate(rects):
                    if r.collidepoint(event.pos):
                        player_count = [1, 1, 2, 3, 4][i]; game_mode = ["SOLO", "BOT", "MULTI", "MULTI", "MULTI"][i]
                        player_names = []; current_phase = PHASE_NAME_INPUT

        elif current_phase == PHASE_NAME_INPUT:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN and active_text.strip() != "":
                    player_names.append(active_text); active_text = ""
                    if len(player_names) == player_count:
                        if game_mode == "BOT": player_names.append("Computer")
                        current_phase = PHASE_ROUND_INPUT
                elif event.key == pygame.K_BACKSPACE: active_text = active_text[:-1]
                else: active_text += event.unicode if len(active_text) < 12 else ""

        elif current_phase == PHASE_ROUND_INPUT:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    max_rounds = int(active_text) if active_text.isdigit() else 0
                    player_scores = [0] * len(player_names); current_player_index = 0; round_counter = 1; active_text = ""; current_phase = PHASE_START
                elif event.key == pygame.K_BACKSPACE: active_text = active_text[:-1]
                elif event.unicode.isdigit(): active_text += event.unicode

        elif current_phase == PHASE_FINAL:
            if event.type == pygame.MOUSEBUTTONDOWN and rolls_left > 0:
                for i in range(5):
                    dx, dy = get_dice_pos(i)
                    if pygame.Rect(dx, dy, 80, 80).collidepoint(event.pos): kept_dice[i] = not kept_dice[i]
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    if rolls_left > 0: current_phase = PHASE_SHAKING; timer = 120
                    else:
                        if not points_already_added:
                            bonus, msg = berechne_wertung(wuerfel_ergebnisse)
                            player_scores[current_player_index] += (bonus if bonus > 0 else sum(wuerfel_ergebnisse))
                        if current_player_index == len(player_names) - 1:
                            if max_rounds != 0 and round_counter >= max_rounds: current_phase = PHASE_GAME_OVER
                            else: round_counter += 1; current_player_index = 0; rolls_left = 3; kept_dice = [False]*5; points_already_added = False; current_phase = PHASE_START
                        else: current_player_index += 1; rolls_left = 3; kept_dice = [False]*5; points_already_added = False; current_phase = PHASE_START
                if event.key == pygame.K_s: phase_vor_dem_speichern = current_phase; current_phase = PHASE_SAVE_NAME
                if event.key == pygame.K_RETURN and rolls_left > 0: rolls_left = 0

        elif event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE and current_phase == PHASE_START:
            phase_vor_dem_speichern = current_phase; current_phase = PHASE_SHAKING; timer = 120
        
        if event.type == pygame.KEYDOWN and event.key == pygame.K_s and current_phase == PHASE_START:
            phase_vor_dem_speichern = current_phase; current_phase = PHASE_SAVE_NAME

    # --- C) UPDATE ---
    if bonus_display_timer > 0: bonus_display_timer -= 1
    if current_phase == PHASE_SHAKING:
        timer -= 1
        if (timer // 5) % 2 == 0:
            aktiver_becher = becher_schief; off_x, off_y = random.randint(-15, 15), random.randint(-10, 10)
        if timer <= 0:
            for i in range(5):
                if not kept_dice[i]: wuerfel_ergebnisse[i] = random.randint(1, 6)
            rolls_left -= 1; current_phase = PHASE_REVEAL; timer = 90 
    elif current_phase == PHASE_REVEAL:
        timer -= 1; aktiver_becher = becher_offen
        if timer <= 0: 
            current_phase = PHASE_FINAL
            bonus, msg = berechne_wertung(wuerfel_ergebnisse)
            if msg != "": bonus_msg = msg; bonus_display_timer = 180
            if rolls_left == 0 and not points_already_added:
                player_scores[current_player_index] += (bonus if bonus > 0 else sum(wuerfel_ergebnisse))
                points_already_added = True

    # --- D) ZEICHNEN ---
    screen.blit(tisch, (0, 0))

    if current_phase == PHASE_MENU:
        screen.blit(menu_bg, (0, 0))
        for r in [start_button_rect, options_button_rect, quit_button_rect]:
            if r.collidepoint(mouse_pos): pygame.draw.rect(screen, (255, 40, 40), r, 4, border_radius=15)

    elif current_phase == PHASE_MODE_SELECT:
        txt = font_large.render("MODUS WÄHLEN", True, GOLD); screen.blit(txt, (SCREEN_WIDTH//2-txt.get_width()//2, 70))
        for i, t in enumerate(["Einzelspieler", "Gegen Computer", "2 Spieler", "3 Spieler", "4 Spieler"]):
            r = pygame.Rect(SCREEN_WIDTH//2-150, 160 + i*70, 300, 50)
            pygame.draw.rect(screen, CASINO_RED if r.collidepoint(mouse_pos) else GRAY, r, border_radius=10); pygame.draw.rect(screen, WHITE, r, 2, border_radius=10)
            ts = font_medium.render(t, True, WHITE); screen.blit(ts, (r.centerx-ts.get_width()//2, r.centery-ts.get_height()//2))

    elif current_phase == PHASE_NAME_INPUT:
        prompt = font_large.render(f"Name für Spieler {len(player_names)+1}:", True, BLACK); screen.blit(prompt, (SCREEN_WIDTH//2 - prompt.get_width()//2, 200))
        pygame.draw.rect(screen, WHITE, (SCREEN_WIDTH//2-200, 300, 400, 60), border_radius=5); pygame.draw.rect(screen, BLACK, (SCREEN_WIDTH//2-200, 300, 400, 60), 2, border_radius=5)
        txt = font_medium.render(active_text + "|", True, BLACK); screen.blit(txt, (SCREEN_WIDTH//2-txt.get_width()//2, 310))

    elif current_phase == PHASE_ROUND_INPUT:
        prompt = font_large.render("Wie viele Runden?", True, BLACK); screen.blit(prompt, (SCREEN_WIDTH//2 - prompt.get_width()//2, 200))
        pygame.draw.rect(screen, WHITE, (SCREEN_WIDTH//2-100, 300, 200, 60), border_radius=5); pygame.draw.rect(screen, BLACK, (SCREEN_WIDTH//2-100, 300, 200, 60), 2, border_radius=5)
        txt = font_medium.render(active_text + "|", True, BLACK); screen.blit(txt, (SCREEN_WIDTH//2-txt.get_width()//2, 310))

    elif current_phase == PHASE_SAVE_NAME:
        prompt = font_large.render("Spielstand benennen:", True, BLACK); screen.blit(prompt, (SCREEN_WIDTH//2 - prompt.get_width()//2, 200))
        pygame.draw.rect(screen, WHITE, (SCREEN_WIDTH//2-200, 300, 400, 60), border_radius=5); pygame.draw.rect(screen, BLACK, (SCREEN_WIDTH//2-200, 300, 400, 60), 2, border_radius=5)
        txt = font_medium.render(save_name_text + "|", True, BLACK); screen.blit(txt, (SCREEN_WIDTH//2-txt.get_width()//2, 310))

    elif current_phase == PHASE_OPTIONS:
        t = font_xl.render("OPTIONEN", True, GOLD); screen.blit(t, (SCREEN_WIDTH//2-t.get_width()//2, 100))
        for r, txt in [(opt_load_rect, "Spiel laden"), (opt_leaderboard_rect, "Bestenliste"), (opt_howto_rect, "Anleitung"), (opt_back_rect, "Zurück")]:
            pygame.draw.rect(screen, CASINO_RED if r.collidepoint(mouse_pos) else GRAY, r, border_radius=10); pygame.draw.rect(screen, WHITE, r, 2, border_radius=10)
            ts = font_medium.render(txt, True, WHITE); screen.blit(ts, (r.centerx-ts.get_width()//2, r.centery-ts.get_height()//2))

    elif current_phase == PHASE_LOAD:
        t = font_large.render("SPIEL LADEN (Max 5)", True, GOLD); screen.blit(t, (SCREEN_WIDTH//2-t.get_width()//2, 50))
        saves = get_save_files()
        for i in range(5):
            r = pygame.Rect(SCREEN_WIDTH//2 - 200, 150 + i*70, 400, 50)
            pygame.draw.rect(screen, CASINO_RED if r.collidepoint(mouse_pos) else GRAY, r, border_radius=10); pygame.draw.rect(screen, WHITE, r, 2, border_radius=10)
            if i < len(saves):
                try:
                    with open(f"saves/{saves[i]}", "r") as f: d = json.load(f); slot_text = d.get("display_name", "Unbenannt")
                except: slot_text = "Fehlerhafte Datei"
            else: slot_text = "--- Leer ---"
            ts = font_small.render(slot_text, True, WHITE); screen.blit(ts, (r.centerx-ts.get_width()//2, r.centery-ts.get_height()//2))
        pygame.draw.rect(screen, CASINO_RED if opt_back_rect.collidepoint(mouse_pos) else GRAY, opt_back_rect, border_radius=10); pygame.draw.rect(screen, WHITE, opt_back_rect, 2, border_radius=10)
        tb = font_medium.render("Zurück", True, WHITE); screen.blit(tb, (opt_back_rect.centerx-tb.get_width()//2, opt_back_rect.centery-tb.get_height()//2))

    elif current_phase == PHASE_LEADERBOARD:
        t = font_large.render("BESTENLISTE (TOP 5)", True, GOLD); screen.blit(t, (SCREEN_WIDTH//2-t.get_width()//2, 50))
        lb_data = []
        if os.path.exists("leaderboard.json"):
            with open("leaderboard.json", "r") as f: lb_data = json.load(f)
        for i in range(5):
            r = pygame.Rect(SCREEN_WIDTH//2 - 200, 150 + i*70, 400, 50)
            pygame.draw.rect(screen, GRAY, r, border_radius=10); pygame.draw.rect(screen, WHITE, r, 2, border_radius=10)
            txt = f"{i+1}. {lb_data[i]['name']} - {lb_data[i]['score']} Pkt" if i < len(lb_data) else f"{i+1}. ---"
            ts = font_small.render(txt, True, WHITE); screen.blit(ts, (r.centerx-ts.get_width()//2, r.centery-ts.get_height()//2))
        pygame.draw.rect(screen, CASINO_RED if opt_back_rect.collidepoint(mouse_pos) else GRAY, opt_back_rect, border_radius=10); pygame.draw.rect(screen, WHITE, opt_back_rect, 2, border_radius=10)
        tb = font_medium.render("Zurück", True, WHITE); screen.blit(tb, (opt_back_rect.centerx-tb.get_width()//2, opt_back_rect.centery-tb.get_height()//2))

    elif current_phase == PHASE_HOWTO:
        lines = ["REGELN", "- 3 Würfe pro Zug", "- Würfel behalten per Klick", "BONUS:", "Pasch (3/4/5): 25/50/100 Pkt", "Full House: 50 | Gr. Straße: 75"]
        for i, l in enumerate(lines):
            ts = font_medium.render(l, True, WHITE); screen.blit(ts, (SCREEN_WIDTH//2-ts.get_width()//2, 150+i*50))
        pygame.draw.rect(screen, CASINO_RED if opt_back_rect.collidepoint(mouse_pos) else GRAY, opt_back_rect, border_radius=10); pygame.draw.rect(screen, WHITE, opt_back_rect, 2, border_radius=10)
        tb = font_medium.render("Zurück", True, WHITE); screen.blit(tb, (opt_back_rect.centerx-tb.get_width()//2, opt_back_rect.centery-tb.get_height()//2))

    elif current_phase == PHASE_GAME_OVER:
        winner_idx = player_scores.index(max(player_scores))
        w_name, w_score = player_names[winner_idx], player_scores[winner_idx]
        if not leaderboard_updated:
            update_leaderboard(w_name, w_score); leaderboard_updated = True
        
        t1 = font_xl.render(w_name, True, GOLD); screen.blit(t1, (SCREEN_WIDTH//2-t1.get_width()//2, 100))
        screen.blit(img_pokal, (SCREEN_WIDTH//2-100, 220))
        # NEUER TEXT
        t2 = font_medium.render(f"Der Sieger ist {w_name} mit {w_score} Punkten!", True, GOLD)
        screen.blit(t2, (SCREEN_WIDTH//2-t2.get_width()//2, 450))

    elif current_phase in [PHASE_START, PHASE_SHAKING, PHASE_REVEAL, PHASE_FINAL]:
        r_txt = font_hint.render(f"RUNDE: {round_counter}", True, GOLD); screen.blit(r_txt, (SCREEN_WIDTH-220, 25))
        if current_phase == PHASE_FINAL:
            bonus, _ = berechne_wertung(wuerfel_ergebnisse); s_val = bonus if bonus > 0 else sum(wuerfel_ergebnisse)
        else:
            temp_dice = [wuerfel_ergebnisse[i] for i in range(5) if kept_dice[i]]
            bonus, _ = berechne_wertung(temp_dice); s_val = bonus if bonus > 0 else sum(temp_dice)
        summe_txt = font_medium.render(f"PUNKTE: {s_val}", True, GOLD); screen.blit(summe_txt, (30, 25))
        for i, name in enumerate(player_names):
            color = GOLD if i == current_player_index else WHITE; score_txt = font_small.render(f"{name}: {player_scores[i]}", True, color)
            pos = [POSITIONS["unten"], POSITIONS["oben"], POSITIONS["rechts"], POSITIONS["links"]][i]; screen.blit([img_player_unten, img_player_oben, img_player_rechts, img_player_links][i], pos)
            screen.blit(score_txt, (pos[0]+130, pos[1]+40) if i==0 else (pos[0], pos[1]+130))
        
        if bonus_display_timer > 0:
            b_surf = font_xl.render(bonus_msg, True, BRIGHT_RED); screen.blit(b_surf, (SCREEN_WIDTH//2-b_surf.get_width()//2, SCREEN_HEIGHT//2-150))
        elif bonus_display_timer <= 0:
            if current_phase == PHASE_START: screen.blit(becher_stehend, POSITIONS["becher"]); screen.blit(font_hint.render("Leertaste: Würfeln", True, WHITE), (30, POSITIONS["hint_y_top"]))
            elif current_phase == PHASE_SHAKING: screen.blit(aktiver_becher, (POSITIONS["becher"][0]+off_x, POSITIONS["becher"][1]+off_y))
            elif current_phase == PHASE_REVEAL: screen.blit(becher_offen, (POSITIONS["becher"][0], POSITIONS["becher"][1]+50))
            elif current_phase == PHASE_FINAL:
                txt = f"Wurf {3-rolls_left+1} | Enter: Beenden" if rolls_left > 0 else "Leertaste: Weiter"
                screen.blit(font_hint.render(txt, True, WHITE), (30, POSITIONS["hint_y_top"]))
        
        screen.blit(font_hint.render(f"ESC: Menü | 'S': Save", True, WHITE), (30, POSITIONS["hint_y_bottom"]))
        screen.blit(font_hint.render(f"{player_names[current_player_index]} ist dran", True, WHITE), (SCREEN_WIDTH//2-150, POSITIONS["hint_y_bottom"]))
        for i in range(5):
            dx, dy = get_dice_pos(i)
            if kept_dice[i] and rolls_left > 0: pygame.draw.rect(screen, GOLD, (dx-5, dy-5, 90, 90), 4, border_radius=5)
            if current_phase == PHASE_FINAL or kept_dice[i]: screen.blit(wuerfel_bilder[wuerfel_ergebnisse[i]-1], (dx, dy))

    pygame.display.flip(); clock.tick(60)

pygame.quit()
os._exit(0)
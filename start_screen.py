import pygame
import sys
import random

# --- 1. SETUP ---
pygame.init()
SCREEN_WIDTH, SCREEN_HEIGHT = 1280, 720
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("BlueMarlin-Würfelspiel")
clock = pygame.time.Clock()

# --- FARBEN & SCHRIFTEN ---
WHITE = (255, 255, 255); BLACK = (0, 0, 0)
CASINO_RED = (180, 0, 0); PLAYER_RED = (180, 40, 40)
GRAY = (50, 50, 50); GOLD = (255, 215, 0)

font_large = pygame.font.SysFont("Arial", 50, bold=True)
font_xl    = pygame.font.SysFont("Arial", 80, bold=True)
font_medium = pygame.font.SysFont("Arial", 32, bold=True)
font_small = pygame.font.SysFont("Arial", 32, bold=True)
font_hint = pygame.font.SysFont("Arial", 26, bold=True)

# --- 2. ASSETS LADEN ---
def load_img(name, size):
    try:
        img = pygame.image.load(f"assets/{name}").convert_alpha()
        return pygame.transform.scale(img, size)
    except:
        print(f"Datei fehlt: assets/{name}"); surf = pygame.Surface(size); surf.fill((255, 0, 0)); return surf

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

current_phase = PHASE_MENU
game_mode = ""; player_count = 1; player_names = []; player_scores = []
current_player_index = 0; round_counter = 1; round_display_timer = 0
max_rounds = 0; active_text = ""; timer = 0

wuerfel_ergebnisse = [1] * 5
kept_dice = [False] * 5 
rolls_left = 3          

start_button_rect = pygame.Rect(510, 502, 260, 49)
quit_button_rect  = pygame.Rect(510, 621, 260, 49)
rect_solo   = pygame.Rect(SCREEN_WIDTH//2 - 150, 160, 300, 50)
rect_bot    = pygame.Rect(SCREEN_WIDTH//2 - 150, 230, 300, 50)
rect_multi2 = pygame.Rect(SCREEN_WIDTH//2 - 150, 300, 300, 50)
rect_multi3 = pygame.Rect(SCREEN_WIDTH//2 - 150, 370, 300, 50)
rect_multi4 = pygame.Rect(SCREEN_WIDTH//2 - 150, 440, 300, 50)

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
W_START_X = 420  
W_HOLD_X = 820   

# --- 4. HAUPTSCHLEIFE ---
running = True
while running:
    mouse_pos = pygame.mouse.get_pos()
    
    # FIX: Variablen vorab definieren für den Draw-Call
    off_x, off_y = 0, 0
    aktiver_becher = becher_stehend

    def get_dice_pos(idx):
        if rolls_left == 0: return (W_START_X + (idx * 90), POSITIONS["wuerfel_y_center"])
        if kept_dice[idx]: return (W_HOLD_X + (idx * 85), POSITIONS["wuerfel_y_hold"])
        return (W_START_X + (idx * 90), POSITIONS["wuerfel_y_center"])
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT: running = False
        
        # --- A) MENÜ-EVENTS ---
        if current_phase == PHASE_MENU:
            if event.type == pygame.MOUSEBUTTONDOWN:
                if start_button_rect.collidepoint(event.pos): current_phase = PHASE_MODE_SELECT
                elif quit_button_rect.collidepoint(event.pos): running = False
            if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                current_phase = PHASE_MODE_SELECT

        elif current_phase == PHASE_MODE_SELECT:
            if event.type == pygame.MOUSEBUTTONDOWN:
                player_names = []; player_scores = []
                if rect_solo.collidepoint(event.pos): game_mode = "SOLO"; player_count = 1; current_phase = PHASE_NAME_INPUT
                elif rect_bot.collidepoint(event.pos): game_mode = "BOT"; player_count = 1; current_phase = PHASE_NAME_INPUT
                elif rect_multi2.collidepoint(event.pos): game_mode = "MULTI"; player_count = 2; current_phase = PHASE_NAME_INPUT
                elif rect_multi3.collidepoint(event.pos): game_mode = "MULTI"; player_count = 3; current_phase = PHASE_NAME_INPUT
                elif rect_multi4.collidepoint(event.pos): game_mode = "MULTI"; player_count = 4; current_phase = PHASE_NAME_INPUT
        
        elif current_phase == PHASE_NAME_INPUT:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN and active_text.strip() != "":
                    player_names.append(active_text); active_text = ""
                    if len(player_names) == player_count:
                        if game_mode == "BOT": player_names.append("Computer")
                        current_phase = PHASE_ROUND_INPUT
                elif event.key == pygame.K_BACKSPACE: active_text = active_text[:-1]
                else: 
                    if len(active_text) < 12 and event.unicode.isprintable(): active_text += event.unicode

        elif current_phase == PHASE_ROUND_INPUT:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    max_rounds = int(active_text) if active_text.isdigit() else 0
                    player_scores = [0] * len(player_names)
                    current_player_index = 0; round_counter = 1; round_display_timer = 120
                    active_text = ""; current_phase = PHASE_START
                elif event.key == pygame.K_BACKSPACE: active_text = active_text[:-1]
                elif event.unicode.isdigit():
                    if len(active_text) < 3: active_text += event.unicode

        # --- B) SPIEL-EVENTS ---
        elif current_phase == PHASE_FINAL:
            if event.type == pygame.MOUSEBUTTONDOWN and rolls_left > 0:
                for i in range(5):
                    dx, dy = get_dice_pos(i)
                    if pygame.Rect(dx, dy, 80, 80).collidepoint(event.pos): kept_dice[i] = not kept_dice[i]
            
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    if rolls_left > 0: current_phase = PHASE_SHAKING; timer = 120
                    else: 
                        player_scores[current_player_index] += sum(wuerfel_ergebnisse)
                        if current_player_index == len(player_names) - 1:
                            if max_rounds != 0 and round_counter >= max_rounds: current_phase = PHASE_GAME_OVER
                            else: round_counter += 1; round_display_timer = 120; current_player_index = 0; rolls_left = 3; kept_dice = [False]*5; current_phase = PHASE_START
                        else:
                            current_player_index += 1; rolls_left = 3; kept_dice = [False]*5; current_phase = PHASE_START
                if event.key == pygame.K_RETURN and rolls_left < 3: rolls_left = 0

        elif current_phase == PHASE_GAME_OVER:
            if event.type == pygame.KEYDOWN or event.type == pygame.MOUSEBUTTONDOWN:
                player_names = []; player_scores = []; round_counter = 1; current_phase = PHASE_MENU

        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE and current_phase == PHASE_START:
                current_phase = PHASE_SHAKING; timer = 120
            if event.key == pygame.K_ESCAPE: current_phase = PHASE_MENU

    # --- C) UPDATE ---
    if round_display_timer > 0: round_display_timer -= 1
    
    if current_phase == PHASE_SHAKING:
        timer -= 1
        if (timer // 5) % 2 == 0:
            aktiver_becher = becher_schief; off_x, off_y = random.randint(-15, 15), random.randint(-10, 10)
        else:
            aktiver_becher = becher_stehend
        
        if timer <= 0:
            for i in range(5):
                if not kept_dice[i]: wuerfel_ergebnisse[i] = random.randint(1, 6)
            rolls_left -= 1; current_phase = PHASE_REVEAL; timer = 90 
    elif current_phase == PHASE_REVEAL:
        timer -= 1; aktiver_becher = becher_offen
        if timer <= 0: current_phase = PHASE_FINAL

    # --- D) ZEICHNEN ---
    screen.fill(BLACK); screen.blit(tisch, (0, 0))

    if current_phase == PHASE_MENU:
        screen.blit(menu_bg, (0, 0))
        for r in [start_button_rect, quit_button_rect]:
            if r.collidepoint(mouse_pos): pygame.draw.rect(screen, (255, 40, 40), r, 4, border_radius=15)

    elif current_phase == PHASE_MODE_SELECT:
        title = font_large.render("SPIELMODUS WÄHLEN", True, GOLD)
        screen.blit(title, (SCREEN_WIDTH//2 - title.get_width()//2, 70))
        buttons = [(rect_solo, "Einzelspieler"), (rect_bot, "Gegen Computer"), (rect_multi2, "2 Spieler"), (rect_multi3, "3 Spieler"), (rect_multi4, "4 Spieler")]
        for r, txt in buttons:
            farbe = CASINO_RED if r.collidepoint(mouse_pos) else GRAY
            pygame.draw.rect(screen, farbe, r, border_radius=10); pygame.draw.rect(screen, WHITE, r, 2, border_radius=10)
            t_surf = font_medium.render(txt, True, WHITE); screen.blit(t_surf, (r.centerx - t_surf.get_width()//2, r.centery - t_surf.get_height()//2))

    elif current_phase == PHASE_NAME_INPUT:
        prompt = font_large.render(f"Name für Spieler {len(player_names)+1}:", True, BLACK)
        screen.blit(prompt, (SCREEN_WIDTH//2 - prompt.get_width()//2, 200))
        input_rect = pygame.Rect(SCREEN_WIDTH//2 - 200, 300, 400, 60)
        pygame.draw.rect(screen, WHITE, input_rect, border_radius=5); pygame.draw.rect(screen, BLACK, input_rect, 2, border_radius=5)
        txt_surf = font_medium.render(active_text + "|", True, BLACK)
        screen.blit(txt_surf, (input_rect.centerx - txt_surf.get_width()//2, input_rect.centery - txt_surf.get_height()//2))

    elif current_phase == PHASE_ROUND_INPUT:
        prompt = font_large.render("Wie viele Runden?", True, BLACK)
        screen.blit(prompt, (SCREEN_WIDTH//2 - prompt.get_width()//2, 200))
        input_rect = pygame.Rect(SCREEN_WIDTH//2 - 100, 300, 200, 60)
        pygame.draw.rect(screen, WHITE, input_rect, border_radius=5); pygame.draw.rect(screen, BLACK, input_rect, 2, border_radius=5)
        txt_surf = font_medium.render(active_text + "|", True, BLACK)
        screen.blit(txt_surf, (input_rect.centerx - txt_surf.get_width()//2, input_rect.centery - txt_surf.get_height()//2))

    elif current_phase == PHASE_GAME_OVER:
        winner_idx = player_scores.index(max(player_scores))
        w_name = player_names[winner_idx]; w_pts = player_scores[winner_idx]
        t1 = font_xl.render(w_name, True, GOLD); screen.blit(t1, (SCREEN_WIDTH//2 - t1.get_width()//2, 150))
        screen.blit(img_pokal, (SCREEN_WIDTH//2 - 100, 220))
        t2 = font_medium.render(f"{w_name} gewinnt wohlverdient mit {w_pts} punkten", True, GOLD)
        screen.blit(t2, (SCREEN_WIDTH//2 - t2.get_width()//2, 450))
        h = font_small.render("Klick zum Hauptmenü", True, WHITE); screen.blit(h, (SCREEN_WIDTH//2-h.get_width()//2, 550))

    elif current_phase in [PHASE_START, PHASE_SHAKING, PHASE_REVEAL, PHASE_FINAL]:
        def get_color(idx): return GOLD if idx == current_player_index else BLACK
        round_txt = font_hint.render(f"RUNDE: {round_counter}{' / ' + str(max_rounds) if max_rounds > 0 else ''}", True, GOLD)
        screen.blit(round_txt, (SCREEN_WIDTH - 220, 25))
        
        s_val = sum(wuerfel_ergebnisse) if current_phase == PHASE_FINAL else sum(wuerfel_ergebnisse[i] for i in range(5) if kept_dice[i])
        summe_txt = font_medium.render(f"PUNKTE: {s_val}", True, GOLD); screen.blit(summe_txt, (30, 25))
        
        # Avatare (Alle 4 Spieler anzeigen)
        screen.blit(img_player_unten, POSITIONS["unten"])
        n1 = font_small.render(f"{player_names[0]}: {player_scores[0]}", True, get_color(0))
        screen.blit(n1, (POSITIONS["unten"][0] + 130, POSITIONS["unten"][1] + 40))
        if game_mode == "BOT" or player_count >= 2:
            screen.blit(img_player_oben, POSITIONS["oben"]); n2 = font_small.render(f"{player_names[1]}: {player_scores[1]}", True, get_color(1))
            screen.blit(n2, (SCREEN_WIDTH//2 - n2.get_width()//2, 160))
        if player_count >= 3:
            screen.blit(img_player_rechts, POSITIONS["rechts"]); n3 = font_small.render(f"{player_names[2]}: {player_scores[2]}", True, get_color(2))
            screen.blit(n3, (POSITIONS["rechts"][0] + 60 - n3.get_width()//2, POSITIONS["rechts"][1] + 130))
        if player_count >= 4:
            screen.blit(img_player_links, POSITIONS["links"]); n4 = font_small.render(f"{player_names[3]}: {player_scores[3]}", True, get_color(3))
            screen.blit(n4, (POSITIONS["links"][0] + 60 - n4.get_width()//2, POSITIONS["links"][1] + 130))

        esc_hint = font_hint.render("ESC: Beenden", True, BLACK); screen.blit(esc_hint, (30, POSITIONS["hint_y_bottom"]))
        h_center = font_hint.render(f"{player_names[current_player_index]} {'hat gewürfelt' if current_phase == PHASE_FINAL else 'ist dran'}", True, BLACK)
        screen.blit(h_center, (SCREEN_WIDTH//2 - h_center.get_width()//2, POSITIONS["hint_y_bottom"]))

        # --- WÜRFEL ZEICHNEN ---
        for i in range(5):
            dx, dy = get_dice_pos(i)
            if kept_dice[i] and rolls_left > 0:
                pygame.draw.rect(screen, GOLD, (dx-5, dy-5, 90, 90), 4, border_radius=5)
                screen.blit(wuerfel_bilder[wuerfel_ergebnisse[i]-1], (dx, dy))
            elif current_phase == PHASE_FINAL:
                screen.blit(wuerfel_bilder[wuerfel_ergebnisse[i]-1], (dx, dy))

        # --- BECHER ZEICHNEN ---
        if current_phase == PHASE_START:
            screen.blit(becher_stehend, POSITIONS["becher"])
            h_action = font_hint.render("Leertaste: Würfeln", True, BLACK); screen.blit(h_action, (30, POSITIONS["hint_y_top"]))
        elif current_phase == PHASE_SHAKING:
            screen.blit(aktiver_becher, (POSITIONS["becher"][0] + off_x, POSITIONS["becher"][1] + off_y))
        elif current_phase == PHASE_REVEAL:
            screen.blit(becher_offen, (POSITIONS["becher"][0], POSITIONS["becher"][1] + 50))
        elif current_phase == PHASE_FINAL:
            txt = f"Leertaste: Wurf {3-rolls_left+1} | Enter: Beenden" if rolls_left > 0 else "Leertaste: Weiter"
            h_action = font_hint.render(txt, True, BLACK); screen.blit(h_action, (30, POSITIONS["hint_y_top"]))

        if round_display_timer > 0:
            ov = font_xl.render(f"RUNDE {round_counter} BEGINNT", True, GOLD)
            screen.blit(ov, (SCREEN_WIDTH//2 - ov.get_width()//2, SCREEN_HEIGHT//2 - 50))

    pygame.display.flip(); clock.tick(60)
pygame.quit(); sys.exit()
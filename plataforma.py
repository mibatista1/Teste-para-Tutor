import pgzrun
import math
import random
from pygame import Rect

# --- Window Settings ---
WIDTH = 800
HEIGHT = 600
TITLE = "Zombie Island - Precise Edition"

# --- Game States ---
MENU = "menu"
PLAYING = "playing"
GAME_OVER = "game_over"

# --- Global Variables ---
game_state = MENU
score = 0
game_speed = 4.5
audio_enabled = True
bg_music_started = False

class MenuButton:
    def __init__(self, text, y_pos):
        self.rect = Rect((WIDTH // 2 - 120, y_pos), (240, 50))
        self.text = text

    def draw(self):
        screen.draw.filled_rect(self.rect, (60, 60, 160))
        screen.draw.text(self.text, center=self.rect.center, color="white", fontsize=30)

    def is_clicked(self, pos):
        return self.rect.collidepoint(pos)

class AnimatedEntity(Actor):
    def __init__(self, prefix, pos, anim_data, start_state):
        super().__init__(f"{prefix}_{start_state}1", pos)
        self.prefix = prefix
        self.anim_data = anim_data 
        self.current_state = start_state
        self.frame_index = 1
        self.anim_timer = 0
        self.anim_speed = 0.12

    def update_animation(self, dt):
        self.anim_timer += dt
        if self.anim_timer >= self.anim_speed:
            self.anim_timer = 0
            max_frames = self.anim_data.get(self.current_state, 1)
            self.frame_index = (self.frame_index % max_frames) + 1
            self.image = f"{self.prefix}_{self.current_state}{self.frame_index}"

class Hero(AnimatedEntity):
    def __init__(self, pos):
        super().__init__("hero", pos, {"run": 3, "idle": 2}, "run")
        self.vel_y = 0
        self.gravity = 0.7
        self.jump_force = -22 # Pulo equilibrado e alto
        self.is_grounded = False

    def update_physics(self):
        self.vel_y += self.gravity
        self.y += self.vel_y

        if self.bottom > HEIGHT - 60:
            self.bottom = HEIGHT - 60
            self.vel_y = 0
            self.is_grounded = True
            self.current_state = "run"
        else:
            self.is_grounded = False
            self.current_state = "idle"

        if keyboard.up and self.is_grounded:
            self.vel_y = self.jump_force
            if audio_enabled:
                try: sounds.jump.play()
                except: pass

class Enemy(AnimatedEntity):
    def __init__(self, prefix, pos, speed):
        super().__init__(prefix, pos, {"walk": 2, "idle": 2}, "walk")
        self.speed = speed
        self.scale = 0.6 # Zumbi em tamanho médio-pequeno

    def move_logic(self):
        self.x -= self.speed

# --- Instances ---
hero = Hero((150, HEIGHT - 100))
enemies = []
btn_start = MenuButton("Start Game", 220)
btn_audio = MenuButton("Audio: ON", 290)
btn_exit = MenuButton("Exit", 360)

def handle_music():
    global bg_music_started
    if audio_enabled and not bg_music_started:
        try:
            sounds.background.play(-1)
            bg_music_started = True
        except: pass
    elif not audio_enabled and bg_music_started:
        try: sounds.background.stop()
        except: pass
        bg_music_started = False

def reset_game():
    global score, enemies, game_speed, game_state
    score = 0
    game_speed = 4.5
    enemies = []
    hero.pos = (150, HEIGHT - 100)
    game_state = PLAYING

def update(dt):
    global game_state, score, game_speed
    
    handle_music()
    
    if game_state == PLAYING:
        score += dt * 10
        game_speed = 4.5 + (score // 1000)
        
        hero.update_physics()
        hero.update_animation(dt)
        
        # Spawn mais espaçado
        if random.randint(0, 100) < 1.5:
            if len(enemies) < 2:
                y_pos = HEIGHT - 92 if random.random() > 0.5 else HEIGHT - 200
                enemies.append(Enemy("enemy", (WIDTH + 100, y_pos), game_speed))
        
        for e in enemies[:]:
            e.move_logic()
            e.update_animation(dt)
            
            # --- SISTEMA DE HITBOX PRECISA ---
            # Criamos retângulos menores para colisão (apenas 50% da largura original)
            hero_hitbox = Rect(0, 0, hero.width * 0.5, hero.height * 0.8)
            hero_hitbox.center = hero.center
            
            enemy_hitbox = Rect(0, 0, e.width * 0.5, e.height * 0.8)
            enemy_hitbox.center = e.center
            
            if hero_hitbox.colliderect(enemy_hitbox):
                # Se os pés do herói estão na parte de cima do zumbi e ele está descendo
                if hero.vel_y > 0 and hero.bottom < e.centery + 10:
                    enemies.remove(e)
                    hero.vel_y = -15
                    score += 150
                    if audio_enabled:
                        try: sounds.jump.play()
                        except: pass
                else:
                    # Se tocar de lado ou estiver subindo, morre
                    game_state = GAME_OVER
                    if audio_enabled:
                        try: sounds.hit.play()
                        except: pass
            
            if e.right < 0:
                enemies.remove(e)

def draw():
    screen.clear()
    if game_state == MENU:
        screen.fill((30, 30, 50))
        screen.draw.text("ZOMBIE ISLAND", center=(WIDTH//2, 120), fontsize=70, color="green")
        btn_start.draw()
        btn_audio.draw()
        btn_exit.draw()
    elif game_state == PLAYING:
        screen.fill((100, 150, 200)) 
        screen.draw.filled_rect(Rect(0, HEIGHT - 60, WIDTH, 60), (70, 50, 30))
        hero.draw()
        for e in enemies:
            e.draw()
        screen.draw.text(f"SCORE: {int(score)}", (20, 20), color="white", fontsize=40)
    elif game_state == GAME_OVER:
        screen.fill((50, 0, 0))
        screen.draw.text("GAME OVER", center=(WIDTH//2, 250), fontsize=80, color="red")
        screen.draw.text(f"SCORE: {int(score)}", center=(WIDTH//2, 330), fontsize=40)
        screen.draw.text("Press SPACE for Menu", center=(WIDTH//2, 400), fontsize=25)

def on_mouse_down(pos):
    global game_state, audio_enabled
    if game_state == MENU:
        if btn_start.is_clicked(pos):
            reset_game()
        elif btn_audio.is_clicked(pos):
            audio_enabled = not audio_enabled
            btn_audio.text = f"Audio: {'ON' if audio_enabled else 'OFF'}"
            handle_music()
        elif btn_exit.is_clicked(pos):
            quit()

def on_key_down(key):
    global game_state
    if game_state == GAME_OVER and key == keys.SPACE:
        game_state = MENU

pgzrun.go()

import random
import sys
import pygame
from pygame.locals import *

# Game Configuration
FPS = 32
SCREEN_WIDTH = 1080
SCREEN_HEIGHT = 512

# Initialize Pygame and seting up the display
pygame.init()
GAME_CLOCK = pygame.time.Clock()
SCREEN = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Makar Sankranti: Kite Flyer")

# Global dictionaries to store assets
ASSETS_IMAGES = {}
ASSETS_SOUNDS = {}

def load_game_resources():
    """ 
    Pulls all images and sounds from the disk. 
    Using a dictionary makes it easy to access them anywhere.
    """
    try:
        # Background and the Kite
        ASSETS_IMAGES['background'] = pygame.transform.scale(pygame.image.load('Sprites/background.png').convert(), (SCREEN_WIDTH, SCREEN_HEIGHT))
        ASSETS_IMAGES['kite'] = pygame.transform.scale(pygame.image.load('Sprites/kite.png').convert_alpha(), (70, 70))
        
        # Obstacles and Scenery
        ASSETS_IMAGES['house'] = pygame.transform.scale(pygame.image.load('Sprites/house.png').convert_alpha(), (150, 150))
        ASSETS_IMAGES['tree'] = pygame.transform.scale(pygame.image.load('Sprites/tree.png').convert_alpha(), (80, 120))
        ASSETS_IMAGES['bird'] = pygame.transform.scale(pygame.image.load('Sprites/pigeon.png').convert_alpha(), (60, 40))
        ASSETS_IMAGES['pole'] = pygame.transform.scale(pygame.image.load('Sprites/pole.png').convert_alpha(), (60, 250))

        # Audio effects
        ASSETS_SOUNDS['flap'] = pygame.mixer.Sound('sounds/swoosh.wav')
        ASSETS_SOUNDS['fail'] = pygame.mixer.Sound('sounds/game_over.wav')
        ASSETS_SOUNDS['score'] = pygame.mixer.Sound('sounds/point.wav')
        ASSETS_SOUNDS['start'] = pygame.mixer.Sound('sounds/game_start.wav')
    except Exception as e:
        print(f"Warning: Some assets couldn't be loaded. Error: {e}")

def render_text(message, font_size, text_color, x_pos, y_pos, has_shadow=True, is_centered=False):
    """ 
    A utility to handle text rendering. 
    The shadow effect helps the text pop against busy backgrounds.
    """
    font = pygame.font.SysFont('Verdana', font_size, bold=True)
    text_surface = font.render(message, True, text_color)
    text_rect = text_surface.get_rect()
    
    if is_centered:
        x_pos = SCREEN_WIDTH/2 - text_rect.width/2
        
    if has_shadow:
        # Draw a dark version slightly offset to simulate a shadow
        shadow_surface = font.render(message, True, (40, 40, 40))
        SCREEN.blit(shadow_surface, (x_pos + 3, y_pos + 3))
        
    SCREEN.blit(text_surface, (x_pos, y_pos))

def generate_obstacle(reference_x):
    """ 
    Pick a random object and place it at a safe distance from the previous one
    to prevent the 'overlapping' glitch.
    """
    possible_obstacles = ['house', 'tree', 'pole', 'bird']
    selected_type = random.choice(possible_obstacles)
    
    # setting offset as spawn_x
    spawn_x = max(SCREEN_WIDTH + 20, reference_x + random.randint(250, 400))
    
    # Birds fly in the sky, everything else on the ground
    if selected_type == 'bird':
        spawn_y = random.randint(50, 250)
    else:
        spawn_y = SCREEN_HEIGHT - ASSETS_IMAGES[selected_type].get_height()
        
    return {'x': spawn_x, 'y': spawn_y, 'type': selected_type, 'has_been_scored': False}

def run_welcome_screen():
    """ Keeps the game in a waiting loop until the user is ready to play """
    while True:
        for event in pygame.event.get():
            if event.type == QUIT or (event.type == KEYDOWN and event.key == K_ESCAPE):
                pygame.quit()
                sys.exit()
            if event.type == KEYDOWN and (event.key in [K_SPACE, K_UP]):
                if 'start' in ASSETS_SOUNDS:
                    ASSETS_SOUNDS['start'].play()
                return
        
        # Draws Menu UI
        SCREEN.blit(ASSETS_IMAGES['background'], (0, 0))
        render_text("MAKAR SANKRANTI", 70, (255, 140, 0), 0, 100, is_centered=True)
        render_text("KITE FLYER", 60, (255, 255, 255), 0, 180, is_centered=True)
        render_text("Press SPACE to Start!", 30, (255, 255, 0), 0, 320, has_shadow=False, is_centered=True)
        
        pygame.display.update()
        GAME_CLOCK.tick(FPS)

def run_main_game():
    """ 
    The core loop where the actual physics, movement, and collisions happen.
    """
    current_score = 0
    kite_x, kite_y = SCREEN_WIDTH // 5, SCREEN_HEIGHT // 2
    
    active_obstacles = []
    last_spawn_x = SCREEN_WIDTH - 200
    for _ in range(6):
        new_obj = generate_obstacle(last_spawn_x)
        active_obstacles.append(new_obj)
        last_spawn_x = new_obj['x']
    
    # Movement Variables
    horizontal_speed = -10
    kite_vertical_velocity = -9
    gravity_constant = 1
    flap_power = -8
    user_just_flapped = False

    while True:
        # Event Handling
        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
                sys.exit()
            if event.type == KEYDOWN and event.key in [K_SPACE, K_UP]:
                if kite_y > 0:
                    kite_vertical_velocity = flap_power
                    user_just_flapped = True
                    if 'flap' in ASSETS_SOUNDS:
                        ASSETS_SOUNDS['flap'].play()

        # Physics & Kite Hitbox
        # We shrink the hitbox slightly for the player
        kite_hitbox = pygame.Rect(kite_x + 15, kite_y + 15, 40, 40)
        
        for item in active_obstacles[:]:
            # Move the obstacle left
            item['x'] += horizontal_speed
            
            # Scoring Logic: check if the kite passed the center of the object
            object_mid = item['x'] + (ASSETS_IMAGES[item['type']].get_width() / 2)
            if object_mid <= (kite_x + 35) and not item['has_been_scored']:
                current_score += 1
                item['has_been_scored'] = True
                if 'score' in ASSETS_SOUNDS:
                    ASSETS_SOUNDS['score'].play()

            # Collision Logic: check against  items (birds and poles)
            if item['type'] in ['bird', 'pole']:
                item_w = ASSETS_IMAGES[item['type']].get_width()
                item_h = ASSETS_IMAGES[item['type']].get_height()
                item_hitbox = pygame.Rect(item['x'], item['y'], item_w, item_h)
                
                if kite_hitbox.colliderect(item_hitbox):
                    if 'fail' in ASSETS_SOUNDS:
                        ASSETS_SOUNDS['fail'].play()
                    return current_score 

        # Ground/Ceiling check
        if kite_y > SCREEN_HEIGHT - 70 or kite_y < 0:
            if 'fail' in ASSETS_SOUNDS:
                ASSETS_SOUNDS['fail'].play()
            return current_score

        # Applying Gravity
        if kite_vertical_velocity < 10 and not user_just_flapped:
            kite_vertical_velocity += gravity_constant
        user_just_flapped = False
        kite_y += kite_vertical_velocity
        
        # List Cleanup & Spawning
        # Remove objects that are far off-screen to save memory
        if active_obstacles[0]['x'] < -200:
            active_obstacles.pop(0)
            
        # Ensures we always have a queue of obstacles coming
        if len(active_obstacles) < 6:
            rightmost_x = max(obj['x'] for obj in active_obstacles)
            active_obstacles.append(generate_obstacle(rightmost_x))

        # Renders Everything
        SCREEN.blit(ASSETS_IMAGES['background'], (0, 0))
        for item in active_obstacles:
            SCREEN.blit(ASSETS_IMAGES[item['type']], (item['x'], item['y']))
        SCREEN.blit(ASSETS_IMAGES['kite'], (kite_x, kite_y))
        
        # Display the UI Score
        render_text(f"SCORE: {current_score}", 40, (255, 255, 255), 0, 30, is_centered=True)

        pygame.display.update()
        GAME_CLOCK.tick(FPS)

def run_game_over_screen(final_score):
    """ Show the final results and wait for a restart signal """
    while True:
        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
                sys.exit()
            if event.type == KEYDOWN and event.key == K_SPACE: 
                if 'start' in ASSETS_SOUNDS:
                    ASSETS_SOUNDS['start'].play()
                return
        
        SCREEN.blit(ASSETS_IMAGES['background'], (0, 0))
        render_text("GAME OVER!", 80, (255, 50, 50), 0, 150, is_centered=True)
        render_text(f"FINAL SCORE: {final_score}", 50, (255, 255, 255), 0, 260, is_centered=True)
        render_text("Press SPACE to Replay!", 30, (255, 255, 0), 0, 360, has_shadow=False, is_centered=True)
        
        pygame.display.update()
        GAME_CLOCK.tick(FPS)

# Execution Point
if __name__ == "__main__":
    load_game_resources()
    while True:
        run_welcome_screen()
        achieved_score = run_main_game()
        run_game_over_screen(achieved_score)
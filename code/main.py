from settings import *
from player import Player
from sprites import *
from pytmx.util_pygame import load_pygame
from groups import AllSprites

from random import randint, choice

class Game:
    def __init__(self):
        # setup
        pygame.init()
        # Initialize mixer explicitly with higher quality
        pygame.mixer.pre_init(44100, -16, 2, 512)
        pygame.mixer.init()
        self.display_surface = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption('The Legend of Gazi Pir')
        self.clock = pygame.time.Clock()
        self.running = True

        # Mission tracking
        self.total_scrolls = 5
        self.total_tigers = 5
        self.collected_scrolls = 0
        self.uncaged_tigers = 0
        self.mission_complete = False
        self.mission_complete_time = 0
        self.show_mission_complete = False

        # UI Font
        self.ui_font = pygame.font.Font(None, 36)
        
        # Intro narration setup
        self.intro_playing = True
        self.intro_start_time = pygame.time.get_ticks()
        self.intro_duration = 79000  # 1 minute 17 seconds in milliseconds
        
        # Intro background and text
        self.intro_background_color = pygame.Color('#f0e2bd')  # Yellowish/brownish white like old paper
        self.intro_font = pygame.font.Font(None, 36)
        self.intro_text = [
            "In the heart of Bengal, where the rivers kiss the forests and the air hums with forgotten songs, there lived a man unlike any other.",
            "His name was Gazi Pir, a warrior, a mystic, and a protector of beasts and people alike.",
            "In a time when fear ruled and the wild was thought to be cursed, Gazi Pir walked among tigers and serpents as brothers. He did not conquer nature, he listened. He did not burn forests, he healed them.",
            "But peace is never left untouched. Greed, ignorance, and power crept in, tearing apart the sacred balance. The creatures he once protected began to vanish, their cries swallowed by fire and steel.",
            "Now, the world cries out again. And Gazi Pir awakens from the silence of legend, summoned to restore what was broken.",
            "This is not just a tale of survival. It is a story of faith, of resistance, of remembering who we were... before we forgot how to live with the Earth.",
            "Step into the forest. The spirits await."
        ]
        
        # Prepare for text scrolling effect
        self.text_surfaces = []
        for line in self.intro_text:
            words = line.split()
            lines = []
            current_line = []
            
            # Wrap text to fit screen width (70% of screen)
            line_width = 0
            max_width = int(WINDOW_WIDTH * 0.7)
            
            for word in words:
                word_surface = self.intro_font.render(word, True, (50, 40, 30))
                word_width = word_surface.get_width()
                
                if line_width + word_width <= max_width:
                    current_line.append(word)
                    line_width += word_width + self.intro_font.size(' ')[0]
                else:
                    lines.append(' '.join(current_line))
                    current_line = [word]
                    line_width = word_width + self.intro_font.size(' ')[0]
            
            if current_line:
                lines.append(' '.join(current_line))
            
            for wrapped_line in lines:
                text_surf = self.intro_font.render(wrapped_line, True, (50, 40, 30))
                self.text_surfaces.append(text_surf)
        
        # Add spacing between paragraphs
        temp_surfaces = []
        for i, surf in enumerate(self.text_surfaces):
            temp_surfaces.append(surf)
            if i < len(self.text_surfaces) - 1 and i + 1 in [len(line.split()) for line in self.intro_text]:
                # Add blank line for paragraph separation
                blank = self.intro_font.render(' ', True, (50, 40, 30))
                temp_surfaces.append(blank)
        
        self.text_surfaces = temp_surfaces

        # Load intro narration audio
        try:
            self.intro_narration = pygame.mixer.Sound(join('audio', 'intro_narration.mp3'))
            self.intro_narration.set_volume(0.7)  # Set volume (adjust as needed)
            print("Successfully loaded intro narration audio")
        except Exception as e:
            print(f"Error loading intro narration: {e}")
            # Fallback - try with different path or file name
            try:
                # Try alternate paths
                alt_paths = [
                    join('audios', 'intro_narration.mp3'),  # You mentioned "audios" folder
                    join('audio', 'intro_narration.wav'),
                    join('audios', 'intro_narration.wav'),
                    'intro_narration.mp3'
                ]
                
                for path in alt_paths:
                    try:
                        print(f"Trying alternate path: {path}")
                        self.intro_narration = pygame.mixer.Sound(path)
                        self.intro_narration.set_volume(0.7)
                        print(f"Successfully loaded from {path}")
                        break
                    except:
                        continue
            except Exception as e2:
                print(f"All fallback attempts failed: {e2}")
                # Create a dummy sound to prevent errors
                self.intro_narration = pygame.mixer.Sound(join('audio', 'shoot.wav'))
                self.intro_narration.set_volume(0)

        # groups 
        self.all_sprites = AllSprites()
        self.collision_sprites = pygame.sprite.Group()
        self.bullet_sprites = pygame.sprite.Group()
        self.enemy_sprites = pygame.sprite.Group()
        self.scroll_sprites = pygame.sprite.Group()
        self.tiger_sprites = pygame.sprite.Group()

        # gun timer
        self.can_shoot = True
        self.shoot_time = 0 
        self.gun_cooldown = 100

        # enemy timer 
        self.enemy_event = pygame.event.custom_type()
        pygame.time.set_timer(self.enemy_event, 300)
        self.spawn_positions = []
        self.used_spawn_positions = set()

        #scroll
        self.reading_scroll = False
        self.scroll_overlay = pygame.Surface((WINDOW_WIDTH - 100, WINDOW_HEIGHT - 100))
        self.scroll_overlay.fill(pygame.Color('#f0e2bd'))
        self.scroll_font = pygame.font.Font(None, 32)
        self.scroll_title_font = pygame.font.Font(None, 42)
        self.scroll_text = ""
        self.scroll_title = ""
        self.scroll_narration = None
        self.current_scroll_id = 0
        
        # audio 
        self.shoot_sound = pygame.mixer.Sound(join('audio', 'shoot.wav'))
        self.shoot_sound.set_volume(0.2)
        self.impact_sound = pygame.mixer.Sound(join('audio', 'impact.ogg'))
        self.tiger_growl = pygame.mixer.Sound(join('audio', 'tiger_growl.mp3'))
        
         

        # Background music
        try:
            self.music = pygame.mixer.Sound(join('audio', 'background_music.mp3'))
            self.music.set_volume(0.3)  # Set at a lower volume (adjust as needed)
            print("Successfully loaded background music")
        except Exception as e:
            print(f"Error loading background music: {e}")
            # Try alternate paths if the first attempt fails
            try:
                alternate_paths = [
                    join('audios', 'background_music.mp3'),
                    'background_music.mp3'
                ]
                for path in alternate_paths:
                    try:
                        print(f"Trying alternate path: {path}")
                        self.music = pygame.mixer.Sound(path)
                        self.music.set_volume(0.3)
                        print(f"Successfully loaded from {path}")
                        break
                    except:
                        continue
            except Exception as e2:
                print(f"Failed to load background music: {e2}")
                # Fallback to empty sound to prevent errors
                self.music = pygame.mixer.Sound(join('audio', 'shoot.wav'))
                self.music.set_volume(0)
        
        # Play background music on loop immediately
        self.music.play(loops=-1)

        # setup
        self.load_images()
        self.setup()
        print(f'Scrolls added: {len(self.scroll_sprites)}')

    def load_images(self):
        self.bullet_surf = pygame.image.load(join('images', 'gun', 'bullet.png')).convert_alpha()

        folders = list(walk(join('images', 'enemies')))[0][1]
        self.enemy_frames = {}
        for folder in folders:
            for folder_path, _, file_names in walk(join('images', 'enemies', folder)):
                self.enemy_frames[folder] = []
                for file_name in sorted(file_names, key = lambda name: int(name.split('.')[0])):
                    full_path = join(folder_path, file_name)
                    surf = pygame.image.load(full_path).convert_alpha()
                    self.enemy_frames[folder].append(surf)
        self.tiger_images = {
            'caged': pygame.image.load(join('images', 'Tiger', 'caged.png')).convert_alpha(),
            'uncaged': pygame.image.load(join('images', 'Tiger', 'uncaged.png')).convert_alpha()
        }

    def render_intro(self):
        # Fill background with old paper color
        self.display_surface.fill(self.intro_background_color)
        
        # Calculate scroll position based on time elapsed
        current_time = pygame.time.get_ticks()
        elapsed = current_time - self.intro_start_time
        
        # Calculate total text height
        total_height = sum(surf.get_height() for surf in self.text_surfaces) + (len(self.text_surfaces) - 1) * 10
        
        # Calculate how far the text should have scrolled
        # Start offscreen at the bottom and scroll up over the duration
        scroll_progress = elapsed / self.intro_duration
        start_y = WINDOW_HEIGHT
        end_y = -total_height
        current_y = start_y + (end_y - start_y) * scroll_progress
        
        # Draw each line of text
        y_pos = current_y
        for surf in self.text_surfaces:
            x_pos = (WINDOW_WIDTH - surf.get_width()) // 2
            self.display_surface.blit(surf, (x_pos, y_pos))
            y_pos += surf.get_height() + 10  # Add spacing between lines
        
        # Check if intro is finished
        if elapsed >= self.intro_duration:
            self.intro_playing = False
            self.intro_narration.stop()  # Stop narration when intro is done
            
        # Handle skip with any key or mouse click
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                self.intro_playing = False
                self.intro_narration.stop()  # Stop narration if game is quit
            elif event.type == pygame.KEYDOWN or event.type == pygame.MOUSEBUTTONDOWN:
                self.intro_playing = False
                self.intro_narration.stop()  # Stop narration if intro is skipped
        
        pygame.display.update()

    def scroll_collision(self):
        scroll_hit_list = pygame.sprite.spritecollide(self.player, self.scroll_sprites, True)
        if scroll_hit_list:
            scroll = scroll_hit_list[0]
            self.reading_scroll = True
            self.scroll_text = scroll.text  # Get text from scroll
            self.scroll_title = scroll.title  # Get title from scroll
            self.current_scroll_id = scroll.scroll_id  # Get scroll ID
            self.scroll_start_time = pygame.time.get_ticks()
            self.collected_scrolls += 1  # Increment collected scrolls counter
            
            # Play scroll narration audio
            try:
                # Stop any currently playing narration
                if self.scroll_narration:
                    self.scroll_narration.stop()
                
                # Load and play the new narration
                narration_path = join('audios', f'scroll{self.current_scroll_id}.mp3')
                self.scroll_narration = pygame.mixer.Sound(narration_path)
                self.scroll_narration.play()
                print(f"Playing scroll {self.current_scroll_id} narration")
            except Exception as e:
                print(f"Error loading scroll narration: {e}")
                # Try alternate paths if the first attempt fails
                try:
                    alternate_paths = [
                        join('audio', f'scroll{self.current_scroll_id}.mp3'),
                        f'scroll{self.current_scroll_id}.mp3'
                    ]
                    for path in alternate_paths:
                        try:
                            self.scroll_narration = pygame.mixer.Sound(path)
                            self.scroll_narration.play()
                            print(f"Successfully loaded from {path}")
                            break
                        except:
                            continue
                except Exception as e2:
                    print(f"Failed to load scroll narration: {e2}")
                    
            self.check_mission_complete()  # Check if mission is complete

    def handle_tigers(self):
        # Check for collisions with tigers
        tiger_collisions = pygame.sprite.spritecollide(self.player, self.tiger_sprites, False)
        
        # If player is colliding with a tiger and right-clicks, uncage it
        if tiger_collisions and pygame.mouse.get_pressed()[2]:
            for tiger in tiger_collisions:
                # Only count if tiger is currently caged
                if tiger.is_caged:
                    self.uncaged_tigers += 1  # Increment uncaged tigers counter
                    self.check_mission_complete()  # Check if mission is complete
                tiger.uncage()

    def check_mission_complete(self):
        # Check if all objectives are complete
        if (self.collected_scrolls >= self.total_scrolls and 
            self.uncaged_tigers >= self.total_tigers and 
            not self.mission_complete):
            self.mission_complete = True
            self.mission_complete_time = pygame.time.get_ticks()
            self.show_mission_complete = True
            print("Mission Complete!")

    def draw_mission_status(self):
        # Draw mission status in top left
        scrolls_text = f"Scrolls: {self.collected_scrolls}/{self.total_scrolls}"
        tigers_text = f"Tigers: {self.uncaged_tigers}/{self.total_tigers}"
        
        # Create text surfaces with shadow for better visibility
        scrolls_shadow = self.ui_font.render(scrolls_text, True, (0, 0, 0))
        scrolls_surface = self.ui_font.render(scrolls_text, True, (255, 255, 255))
        tigers_shadow = self.ui_font.render(tigers_text, True, (0, 0, 0))
        tigers_surface = self.ui_font.render(tigers_text, True, (255, 255, 255))
        
        # Draw shadow text slightly offset
        self.display_surface.blit(scrolls_shadow, (22, 22))
        self.display_surface.blit(scrolls_surface, (20, 20))
        self.display_surface.blit(tigers_shadow, (22, 62))
        self.display_surface.blit(tigers_surface, (20, 60))
        
        # Draw mission complete message if applicable
        if self.show_mission_complete:
            # Center of screen
            complete_text = "MISSION COMPLETE!"
            complete_surface = pygame.font.Font(None, 72).render(complete_text, True, (255, 215, 0))
            complete_rect = complete_surface.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 - 50))
            
            # Create a semi-transparent background
            overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 128))  # Semi-transparent black
            self.display_surface.blit(overlay, (0, 0))
            
            # Draw the text with shadow for better visibility
            shadow_surface = pygame.font.Font(None, 72).render(complete_text, True, (0, 0, 0))
            shadow_rect = shadow_surface.get_rect(center=(WINDOW_WIDTH // 2 + 3, WINDOW_HEIGHT // 2 - 47))
            self.display_surface.blit(shadow_surface, shadow_rect)
            self.display_surface.blit(complete_surface, complete_rect)
            
            # Auto-hide after 5 seconds
            if pygame.time.get_ticks() - self.mission_complete_time > 20000:
                self.show_mission_complete = False

    def input(self):
        if pygame.mouse.get_pressed()[0] and self.can_shoot:
            self.shoot_sound.play()
            pos = self.gun.rect.center + self.gun.player_direction * 50
            Bullet(self.bullet_surf, pos, self.gun.player_direction, (self.all_sprites, self.bullet_sprites))
            self.can_shoot = False
            self.shoot_time = pygame.time.get_ticks()

    def gun_timer(self):
        if not self.can_shoot:
            current_time = pygame.time.get_ticks()
            if current_time - self.shoot_time >= self.gun_cooldown:
                self.can_shoot = True

    def setup(self):
        map = load_pygame(join('data', 'maps', 'world.tmx'))

        for x, y, image in map.get_layer_by_name('Ground').tiles():
            Sprite((x * TILE_SIZE,y * TILE_SIZE), image, self.all_sprites)
        
        for obj in map.get_layer_by_name('Objects'):
            CollisionSprite((obj.x, obj.y), obj.image, (self.all_sprites, self.collision_sprites))
        
        for obj in map.get_layer_by_name('Collisions'):
            CollisionSprite((obj.x, obj.y), pygame.Surface((obj.width, obj.height)), self.collision_sprites)
        
        # Define scroll titles and detailed texts
        scroll_titles = [
            "The Guardian of the Forest",
            "The Man Who Rode Tigers",
            "The Protector of the People",
            "His Healing Touch",
            "The Legend Lives On"
        ]
        
        scroll_texts = [
            "Long ago, when tigers roamed freely and men feared the Sundarbans, Gazi Pir arrived not with a sword, but with peace in his heart. He tamed the beasts not through force, but through faith. It is said that tigers bowed their heads before him, recognizing his spirit as one of the wild and the divine. Even today, when a tiger spares a traveler, they whisper, 'Gazi is watching.'",
            
            "People say Gazi Pir rode a tiger the way others ride horses.\nWearing green and gold, he would travel through the mangrove forests, watching over those who lived there.\nThe forests could be wild and unpredictable, but Gazi Pir brought calm and protection wherever he went.\nSome believed the tigers followed him not out of fear, but because he understood them.\nHe didn't see them as dangerous animals; he saw them as protectors of nature, just like him.\nHe moved through the trees like he belonged there, quietly helping those in need.\nHis story lives on in quiet whispers, carried by the wind and remembered by the forest.",
            
            "When the rivers swelled and floods came close to the villages, people would look to Gazi Pir.\nThey say he would stand by the water's edge, lifting his arms to the sky as if in quiet prayer.\nSomehow, the waters would settle. The rains would ease. Crops began to grow again.\nTo those who lived near the forest and rivers, this felt like hope.\nThey believed Gazi Pir could connect with nature, not through power, but through understanding.\nHe didn't fight the storms, but asked for peace in a way only he could.\nEven now, before the heavy rains of monsoon, many farmers still pause to remember him.\nSome leave small offerings, some whisper a prayer, not out of fear, but from old habits of trust.\nBecause once, long ago, someone listened when the rivers spoke.",
            
            "In many villages near the Sundarbans, stories are still told of Gazi Pir's healing touch. It's said that when someone was bitten by a snake, their family would place soil from near his shrine into water, and give it to the person to drink. Sometimes, they would tie a thread around the bite, whispering his name as a prayer. People believed that Gazi's blessings could draw out the poison, especially when help was far away.\nEven today, some still visit his shrines during illness, lighting candles or offering flowers. Whether through faith or tradition, the belief in Gazi Pir's protection has been passed down for generations and remembered in the quiet hopes of those who seek comfort in his name.",
            
            "Some people say Gazi Pir never truly passed away.\nThat he still moves through the Sundarbans, in the quiet of the trees, in the sound of the wind, and even in the call of a tiger.\nHis presence isn't loud or grand, but something that people feel when they walk through the forests or sit by the rivers.\nThere are small shrines to him here and simple places where people light candles or leave flowers. They don't ask for miracles. Just protection, guidance, maybe a little peace.\nThe scroll you hold now is just one part of a bigger story.\nOthers have pieces too, like old songs, quiet prayers, and memories passed down over time.\nGazi Pir's story doesn't live in one place. It continues through those who still remember and share it.\nNot in books, but in the people who quietly carry his story with them."
        ]

        scroll_index = 0
        for obj in map.get_layer_by_name('Entities'):
            if obj.name == 'Player':
                self.player = Player((obj.x,obj.y), self.all_sprites, self.collision_sprites)
                self.gun = Gun(self.player, self.all_sprites)
            elif obj.name == 'Enemy':
                self.spawn_positions.append((obj.x, obj.y))
            elif obj.name == 'Scroll':
                if scroll_index < len(scroll_texts):
                    scroll_image = pygame.image.load(join('images', 'scroll', '0.png')).convert_alpha()
                    ScrollSprite(
                        (obj.x, obj.y), 
                        scroll_image, 
                        (self.all_sprites, self.scroll_sprites), 
                        scroll_texts[scroll_index],
                        scroll_titles[scroll_index],
                        scroll_index + 1  # Scroll ID (1-5)
                    )
                    scroll_index += 1
            elif obj.name == 'Tiger':
                Tiger((obj.x, obj.y), self.tiger_images, 
                    (self.all_sprites, self.tiger_sprites), 
                    self.collision_sprites,
                    self.tiger_growl) 
    def bullet_collision(self):
        if self.bullet_sprites:
            for bullet in self.bullet_sprites:
                collision_sprites = pygame.sprite.spritecollide(bullet, self.enemy_sprites, False, pygame.sprite.collide_mask)
                if collision_sprites:
                    self.impact_sound.play()
                    for sprite in collision_sprites:
                        sprite.destroy()
                    bullet.kill()

    def player_collision(self):
        if pygame.sprite.spritecollide(self.player, self.enemy_sprites, False, pygame.sprite.collide_mask):
            self.running = False

    def run(self):
        # Play intro sequence first
        narration_started = False
        while self.intro_playing and self.running:
            self.clock.tick(60)  # Cap at 60 FPS during intro
            
            # Start intro narration if it's not already playing
            if not narration_started:
                try:
                    channel = self.intro_narration.play()
                    print("Playing intro narration...")
                    narration_started = True
                except Exception as e:
                    print(f"Error playing intro narration: {e}")
                    narration_started = True  # Don't try again
                
            self.render_intro()
            
        # Main game loop
        while self.running:
            # dt 
            dt = self.clock.tick() / 1000

            # event loop 
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                if event.type == self.enemy_event:
                    available_positions = [pos for pos in self.spawn_positions if pos not in self.used_spawn_positions]
                    if available_positions:
                        spawn_pos = choice(available_positions)
                        self.used_spawn_positions.add(spawn_pos)
                        Enemy(spawn_pos, choice(list(self.enemy_frames.values())), (self.all_sprites, self.enemy_sprites), self.player, self.collision_sprites)

            # update 
            self.gun_timer()
            self.input()
            self.all_sprites.update(dt)
            self.bullet_collision()
            self.scroll_collision()
            self.handle_tigers()
            # self.player_collision()

            # draw
            self.display_surface.fill('black')
            self.all_sprites.draw(self.player.rect.center)
            
            # Draw mission status (scrolls/tigers counters)
            self.draw_mission_status()

            # Draw scroll overlay
            if self.reading_scroll:
                # Draw scroll background box
                overlay_rect = self.scroll_overlay.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2))
                self.display_surface.blit(self.scroll_overlay, overlay_rect)
                
                # Draw scroll title
                title_surface = self.scroll_title_font.render(self.scroll_title, True, (139, 69, 19))  # Brown color
                title_rect = title_surface.get_rect(midtop=(overlay_rect.centerx, overlay_rect.top + 20))
                self.display_surface.blit(title_surface, title_rect)
                
                # Draw close button
                close_button = pygame.Rect(0, 0, 100, 40)
                close_button.bottomright = (overlay_rect.right - 20, overlay_rect.bottom - 20)
                pygame.draw.rect(self.display_surface, (139, 69, 19), close_button, border_radius=5)
                close_text = self.scroll_font.render("Close", True, (255, 255, 255))
                close_text_rect = close_text.get_rect(center=close_button.center)
                self.display_surface.blit(close_text, close_text_rect)
                
                # Check for close button click
                mouse_pos = pygame.mouse.get_pos()
                mouse_clicked = pygame.mouse.get_pressed()[0]
                if close_button.collidepoint(mouse_pos) and mouse_clicked:
                    self.reading_scroll = False
                    if self.scroll_narration:
                        self.scroll_narration.stop()
                
                # Text wrapping for scroll content
                max_width = overlay_rect.width - 60  # Margin on both sides
                words = self.scroll_text.split()
                lines = []
                current_line = []
                line_width = 0
                
                for word in words:
                    # Handle newline characters in the text
                    if "\n" in word:
                        sub_words = word.split("\n")
                        if current_line and sub_words[0]:  # Add first part to current line
                            current_line.append(sub_words[0])
                            lines.append(" ".join(current_line))
                        elif sub_words[0]:  # First part is a line by itself
                            lines.append(sub_words[0])
                            
                        # Add middle parts as separate lines
                        for i in range(1, len(sub_words) - 1):
                            if sub_words[i]:
                                lines.append(sub_words[i])
                                
                        # Start new line with last part if it exists
                        current_line = [sub_words[-1]] if sub_words[-1] else []
                        line_width = self.scroll_font.size(sub_words[-1])[0] if sub_words[-1] else 0
                        continue
                        
                    word_width = self.scroll_font.size(word)[0]
                    space_width = self.scroll_font.size(" ")[0]
                    
                    if line_width + word_width + (space_width if current_line else 0) <= max_width:
                        current_line.append(word)
                        line_width += word_width + (space_width if line_width > 0 else 0)
                    else:
                        if current_line:  # Only add if there's text
                            lines.append(" ".join(current_line))
                        current_line = [word]
                        line_width = word_width
                
                # Add the last line if there is one
                if current_line:
                    lines.append(" ".join(current_line))
                
                # Draw wrapped text
                y_offset = title_rect.bottom + 20
                for line in lines:
                    if line.strip():  # Only render non-empty lines
                        line_surf = self.scroll_font.render(line, True, (0, 0, 0))
                        line_rect = line_surf.get_rect(midtop=(overlay_rect.centerx, y_offset))
                        self.display_surface.blit(line_surf, line_rect)
                        y_offset += line_surf.get_height() + 5  # Space between lines

            # update display AFTER everything is drawn
            pygame.display.update()
            
        # Stop music when game ends
        self.music.stop()
        pygame.quit()

if __name__ == '__main__':
    game = Game()
    game.run()
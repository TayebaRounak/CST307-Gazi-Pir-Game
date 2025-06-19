from settings import * 
from math import atan2, degrees
from random import randint

class Sprite(pygame.sprite.Sprite):
    def __init__(self, pos, surf, groups):
        super().__init__(groups)
        self.image = surf
        self.rect = self.image.get_frect(topleft = pos)
        self.ground = True

class CollisionSprite(pygame.sprite.Sprite):
    def __init__(self, pos, surf, groups):
        super().__init__(groups)
        self.image = surf
        self.rect = self.image.get_frect(topleft = pos)

class Gun(pygame.sprite.Sprite):
    def __init__(self, player, groups):
        # player connection
        self.player = player
        self.distance = 70  # REDUCED FROM 140 to 70
        self.player_direction = pygame.Vector2(0,1)

        # sprite setup 
        super().__init__(groups)
        self.gun_surf = pygame.image.load(join('images', 'gun', 'gun.png')).convert_alpha()
        self.image = self.gun_surf
        self.rect = self.image.get_frect(center = self.player.rect.center + self.player_direction * self.distance)

    def get_direction(self):
        mouse_pos = pygame.Vector2(pygame.mouse.get_pos())
        player_pos = pygame.Vector2(WINDOW_WIDTH / 2, WINDOW_HEIGHT / 2)
        direction_vector = mouse_pos - player_pos
        if direction_vector.length() != 0:
            self.player_direction = direction_vector.normalize()
        else:
            self.player_direction = pygame.Vector2()

    def rotate_gun(self):
        angle = degrees(atan2(self.player_direction.x, self.player_direction.y)) - 90
        if self.player_direction.x > 0:
            self.image = pygame.transform.rotozoom(self.gun_surf, angle, 1)
        else:
            self.image = pygame.transform.rotozoom(self.gun_surf, abs(angle), 1)
            self.image = pygame.transform.flip(self.image, False, True)
        
        # Get new rect for rotated image but keep the center position
        old_center = self.rect.center
        self.rect = self.image.get_frect()
        self.rect.center = old_center

    def update(self, _):
        self.get_direction()
        self.rotate_gun()
        # Ensure the gun stays at a consistent distance from player
        self.rect.center = self.player.rect.center + self.player_direction * self.distance


class Bullet(pygame.sprite.Sprite):
    def __init__(self, surf, pos, direction, groups):
        super().__init__(groups)
        self.image = surf 
        self.rect = self.image.get_frect(center = pos)
        self.spawn_time = pygame.time.get_ticks()
        self.lifetime = 1000

        self.direction = direction 
        self.speed = 1200 
    
    def update(self, dt):
        self.rect.center += self.direction * self.speed * dt

        if pygame.time.get_ticks() - self.spawn_time >= self.lifetime:
            self.kill()

class Enemy(pygame.sprite.Sprite):
    def __init__(self, pos, frames, groups, player, collision_sprites):
        super().__init__(groups)
        self.player = player

        # image 
        self.frames, self.frame_index = frames, 0 
        self.image = self.frames[self.frame_index]
        self.animation_speed = 6

        # rect 
        self.rect = self.image.get_frect(center = pos)
        self.hitbox_rect = self.rect.inflate(-20,-40)
        self.collision_sprites = collision_sprites
        self.direction = pygame.Vector2()
        self.speed = 200

        # timer 
        self.death_time = 0
        self.death_duration = 400
    
    def animate(self, dt):
        self.frame_index += self.animation_speed * dt
        self.image = self.frames[int(self.frame_index) % len(self.frames)]

    def move(self, dt):
        # get direction 
        player_pos = pygame.Vector2(self.player.rect.center)
        enemy_pos = pygame.Vector2(self.rect.center)
        direction_vector = player_pos - enemy_pos
        if direction_vector.length() != 0:
            self.direction = direction_vector.normalize()
        else:
            self.direction = pygame.Vector2()

        # update the rect position + collision
        self.hitbox_rect.x += self.direction.x * self.speed * dt
        self.collision('horizontal')
        self.hitbox_rect.y += self.direction.y * self.speed * dt
        self.collision('vertical')
        self.rect.center = self.hitbox_rect.center

    def collision(self, direction):
        for sprite in self.collision_sprites:
            if sprite.rect.colliderect(self.hitbox_rect):
                if direction == 'horizontal':
                    if self.direction.x > 0: self.hitbox_rect.right = sprite.rect.left
                    if self.direction.x < 0: self.hitbox_rect.left = sprite.rect.right
                else:
                    if self.direction.y < 0: self.hitbox_rect.top = sprite.rect.bottom
                    if self.direction.y > 0: self.hitbox_rect.bottom = sprite.rect.top

    def destroy(self):
        # start a timer 
        self.death_time = pygame.time.get_ticks()
        # change the image 
        surf = pygame.mask.from_surface(self.frames[0]).to_surface()
        surf.set_colorkey('black')
        self.image = surf
    
    def death_timer(self):
        if pygame.time.get_ticks() - self.death_time >= self.death_duration:
            self.kill()

    def update(self, dt):
        if self.death_time == 0:
            self.move(dt)
            self.animate(dt)
        else:
            self.death_timer()

class Tiger(pygame.sprite.Sprite):
    def __init__(self, pos, images, groups, collision_sprites,growl_sound=None):
        super().__init__(groups)
        # Load images
        self.caged_image = images['caged']
        self.uncaged_image = images['uncaged']
        
        # Start as caged
        self.is_caged = True
        self.image = self.caged_image
        self.rect = self.image.get_frect(center=pos)
        
        # Movement properties
        self.hitbox_rect = self.rect.inflate(-20, -20)
        self.collision_sprites = collision_sprites
        self.direction = pygame.Vector2(0, 0)
        self.speed = 100  # Slower than enemies
        
        # Timer for changing direction
        self.direction_change_time = 0
        self.growl_sound = growl_sound
        self.direction_change_cooldown = 2000  # Change direction every 2 seconds
        
    def uncage(self):
        if self.is_caged:
            self.is_caged = False
            self.image = self.uncaged_image
            # Set initial random direction
            self.change_direction()
            
        if self.growl_sound:
                self.growl_sound.play()
    def change_direction(self):
        # Random direction
        angle = randint(0, 360)
        self.direction = pygame.Vector2(pygame.math.Vector2(1, 0).rotate(angle).normalize())
    
    def move(self, dt):
        if not self.is_caged:
            # Check if it's time to change direction
            current_time = pygame.time.get_ticks()
            if current_time - self.direction_change_time >= self.direction_change_cooldown:
                self.change_direction()
                self.direction_change_time = current_time
            
            # Move the tiger
            self.hitbox_rect.x += self.direction.x * self.speed * dt
            self.collision('horizontal')
            self.hitbox_rect.y += self.direction.y * self.speed * dt
            self.collision('vertical')
            self.rect.center = self.hitbox_rect.center
    
    def collision(self, direction):
        for sprite in self.collision_sprites:
            if sprite.rect.colliderect(self.hitbox_rect):
                if direction == 'horizontal':
                    if self.direction.x > 0: self.hitbox_rect.right = sprite.rect.left
                    if self.direction.x < 0: self.hitbox_rect.left = sprite.rect.right
                    # Bounce in opposite direction
                    self.direction.x *= -1
                else:
                    if self.direction.y < 0: self.hitbox_rect.top = sprite.rect.bottom
                    if self.direction.y > 0: self.hitbox_rect.bottom = sprite.rect.top
                    # Bounce in opposite direction
                    self.direction.y *= -1
    
    def update(self, dt):
        self.move(dt)


class ScrollSprite(pygame.sprite.Sprite):
    def __init__(self, pos, image, groups, text,title,idx):
        super().__init__(groups)
        self.image = image
        self.rect = self.image.get_rect(topleft=pos)
        self.text = text 
        self.title = title
        self.scroll_id = idx

        


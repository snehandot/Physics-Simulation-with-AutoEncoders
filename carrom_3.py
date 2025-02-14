import pygame
import sys
import math
import pandas as pd
import random

# Initialize Pygame
pygame.init()

# Screen dimensions
width, height = 100,100
screen = pygame.display.set_mode((width, height))  # Extra space for the scrollable interface
pygame.display.set_caption('Carrom Simulation')

# Colors
white = (255, 255, 255)
black = (0, 0, 0)
skin = (222, 198, 174)

# Font for displaying text
font = pygame.font.SysFont(None, 18)

# DataFrame to store collision data
collision_data = pd.DataFrame(columns=['Coin1 Pos', 'Coin1 Vel', 'Coin2 Pos', 'Coin2 Vel', 'Initial Relative Velocity', 'Final Relative Velocity'])

# Coin class
class Coin:
    def __init__(self, pos, vel, radius=10, cor=1):
        self.color = white  # Set all coins to white
        self.pos = pos
        self.vel = vel
        self.radius = radius
        self.cor = cor  # Coefficient of restitution

    def move(self):
            max_movement = 0.5  # Maximum movement per frame

            # Calculate the maximum possible movement based on current velocity
            max_movement_x = abs(self.vel[0])
            max_movement_y = abs(self.vel[1])

            # Scale down the velocity if necessary to limit movement
            if max_movement_x > max_movement:
                self.vel[0] = self.vel[0] / max_movement_x * max_movement
            if max_movement_y > max_movement:
                self.vel[1] = self.vel[1] / max_movement_y * max_movement
            self.pos[0] += self.vel[0]
            self.pos[1] += self.vel[1]
            print(self.pos)

    def apply_deceleration(self, deceleration_rate=0.99):
        self.vel[0] *= deceleration_rate
        self.vel[1] *= deceleration_rate

    def draw(self, screen):
        pygame.draw.circle(screen, self.color, (int(self.pos[0]), int(self.pos[1])), self.radius)

    def handle_wall_collision(self, width, height):
        if self.pos[0] - self.radius <= 0 or self.pos[0] + self.radius >= width:
            self.vel[0] = -self.vel[0]
        if self.pos[1] - self.radius <= 0 or self.pos[1] + self.radius >= height:
            self.vel[1] = -self.vel[1]

    def handle_coin_collision(self, other):
        global collision_data
        dist = math.hypot(self.pos[0] - other.pos[0], self.pos[1] - other.pos[1])
        if dist < 2 * self.radius:
            # Normal and tangent vectors
            normal = [(other.pos[0] - self.pos[0]) / dist, (other.pos[1] - self.pos[1]) / dist]

            # Initial normal velocities
            self_normal_velocity = normal[0] * self.vel[0] + normal[1] * self.vel[1]
            other_normal_velocity = normal[0] * other.vel[0] + normal[1] * other.vel[1]

            # Initial relative velocity for collision data
            initial_relative_velocity = abs(self_normal_velocity - other_normal_velocity)

            # New velocities with COR
            new_self_normal_velocity = (self_normal_velocity * (1 - self.cor) + other_normal_velocity * (1 + self.cor)) / 2
            new_other_normal_velocity = (self_normal_velocity * (1 + self.cor) + other_normal_velocity * (1 - self.cor)) / 2

            # Update velocities
            self.vel[0] += (new_self_normal_velocity - self_normal_velocity) * normal[0]
            self.vel[1] += (new_self_normal_velocity - self_normal_velocity) * normal[1]
            other.vel[0] += (new_other_normal_velocity - other_normal_velocity) * normal[0]
            other.vel[1] += (new_other_normal_velocity - other_normal_velocity) * normal[1]

            # Final relative velocity for collision data
            final_relative_velocity = abs(new_self_normal_velocity - new_other_normal_velocity)

            # Record collision data
            collision_data = pd.concat([collision_data, pd.DataFrame({
                'Coin1 Pos': [self.pos.copy()], 'Coin1 Vel': [self.vel.copy()],
                'Coin2 Pos': [other.pos.copy()], 'Coin2 Vel': [other.vel.copy()],
                'Initial Relative Velocity': [initial_relative_velocity],
                'Final Relative Velocity': [final_relative_velocity]
            })], ignore_index=True)

# Create coins with random initial velocities
def create_coins(num_coins, screen_width, screen_height):
    coins = []
    for i in range(num_coins):
        pos = [random.randint(20, screen_width - 20), random.randint(20, screen_height - 20)]
        vel = [random.uniform(-3, 3), random.uniform(-3, 3)]  # Random initial velocity range
        coins.append(Coin(pos, vel))
    return coins

# Draw the carrom board
def draw_carrom_board(screen, width, height):
    pygame.draw.rect(screen, white, (25, 25, width - 50, height - 50), 5)

# Display coin data in a scrollable area
def display_coin_data(screen, coins, scroll_offset):
    #y_offset = height + 10 - scroll_offset
    #for i, coin in enumerate(coins):
    #    text = f"Coin {i+1}: Vel=({round(coin.vel[0], 2)}, {round(coin.vel[1], 2)})"
    #    img = font.render(text, True, black)
    #    screen.blit(img, (10, y_offset))
    #    y_offset += 20
    pass

# Main game loop
clock = pygame.time.Clock()
running = True
num_coins = 2  # Adjust for more coins as needed
coins = create_coins(num_coins, width, height)  # Create coins with randomized initial velocities
scroll_offset = 0
scroll_speed = 10

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        
    # Move coins
    for coin in coins:
        coin.move()
        #coin.apply_deceleration()

    # Handle wall collisions
    for coin in coins:
        coin.handle_wall_collision(width, height)

    # Handle coin collisions
    for i in range(len(coins)):
        for j in range(i + 1, len(coins)):
            coins[i].handle_coin_collision(coins[j])

    # Clear the screen
    screen.fill(skin)

    # Draw the carrom board
    draw_carrom_board(screen, width, height)

    # Draw coins
    for coin in coins:
        coin.draw(screen)

    display_coin_data(screen, coins, scroll_offset)

    # Update the display
    pygame.display.flip()

    # Cap the frame rate
    clock.tick(60)

pygame.quit()
sys.exit()

# After quitting, display the recorded collision data
print(collision_data)

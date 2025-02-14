import pygame
import sys
import math
import pandas as pd
import random

pygame.init()
width, height = 400, 400
screen = pygame.display.set_mode((width, height))
pygame.display.set_caption('Carrom Simulation')

white = (255, 255, 255)
black = (0, 0, 0)
skin = (222, 198, 174)

font = pygame.font.SysFont(None, 18)
class Coin:
    def __init__(self, pos, vel, radius=10, cor=1):
        self.color = white
        self.pos = pos
        self.vel = vel
        self.radius = radius
        self.cor = cor

    def move(self):
        max_movement = 0.75  # Maximum movement per frame
        max_movement_x = abs(self.vel[0])
        max_movement_y = abs(self.vel[1])

        # Scale down the velocity if necessary to limit movement
        if max_movement_x > max_movement:
            self.vel[0] = self.vel[0] / max_movement_x * max_movement
        if max_movement_y > max_movement:
            self.vel[1] = self.vel[1] / max_movement_y * max_movement

        # Update the position based on the scaled velocity
        self.pos[0] += self.vel[0]
        self.pos[1] += self.vel[1]

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
        dist = math.hypot(self.pos[0] - other.pos[0], self.pos[1] - other.pos[1])
        if dist < 2 * self.radius:
            # Normal and tangent vectors
            normal = [(other.pos[0] - self.pos[0]) / dist, (other.pos[1] - self.pos[1]) / dist]

            # Initial normal velocities
            self_normal_velocity = normal[0] * self.vel[0] + normal[1] * self.vel[1]
            other_normal_velocity = normal[0] * other.vel[0] + normal[1] * other.vel[1]

            # New velocities with COR
            new_self_normal_velocity = (self_normal_velocity * (1 - self.cor) + other_normal_velocity * (1 + self.cor)) / 2
            new_other_normal_velocity = (self_normal_velocity * (1 + self.cor) + other_normal_velocity * (1 - self.cor)) / 2

            # Update velocities
            self.vel[0] += (new_self_normal_velocity - self_normal_velocity) * normal[0]
            self.vel[1] += (new_self_normal_velocity - self_normal_velocity) * normal[1]
            other.vel[0] += (new_other_normal_velocity - other_normal_velocity) * normal[0]
            other.vel[1] += (new_other_normal_velocity - other_normal_velocity) * normal[1]

# Create coins with random initial velocities
def create_coins(num_coins, screen_width, screen_height):
    coins = []
    for i in range(num_coins):
        while True:
            pos = [random.randint(20, screen_width - 20), random.randint(20, screen_height - 20)]
            overlap = False
            for coin in coins:
                if math.hypot(pos[0] - coin.pos[0], pos[1] - coin.pos[1]) < 2 * coin.radius:
                    overlap = True
                    break
            if not overlap:
                break
        vel = [random.uniform(-3, 3), random.uniform(-3, 3)]
        coins.append(Coin(pos, vel))
    return coins

# Draw the carrom board
def draw_carrom_board(screen, width, height):
    pygame.draw.rect(screen, white, (25, 25, width - 50, height - 50), 5)

# Main game loop
clock = pygame.time.Clock()
running = True
num_coins = 15
coins = create_coins(num_coins, width, height)

# Initialize a list to store coin positions for each frame
frame_data = []
frames=0
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_q:
                # Create a DataFrame from the collected data
                df = pd.DataFrame(frame_data, columns=[f"Coin {i}" for i in range(num_coins)])

                # Save the DataFrame to a CSV file
                df.to_csv("coin_positions.csv", index=True)

                running = False

    # Move coins
    for coin in coins:
        coin.move()

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

    # Collect coin positions for the current frame
    frame_positions = []
    for coin in coins:
        tem=coin.pos.copy()
        frame_positions.append(("--".join(str(x) for x in tem)))

    frame_data.append(frame_positions)
    frames+=1
    print(f"\rNo of frames: {frames}",end='')

    # Draw coins
    for coin in coins:
        coin.draw(screen)

    # Update the display
    pygame.display.flip()

    # Cap the frame rate
    clock.tick(600000)

pygame.quit()
sys.exit()

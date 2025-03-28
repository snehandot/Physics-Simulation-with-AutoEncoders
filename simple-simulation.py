import pygame
import sys
import math

# Initialize Pygame
pygame.init()

# Screen dimensions
width, height = 400, 400
screen = pygame.display.set_mode((width, height))
pygame.display.set_caption('Carrom Simulation')

# Colors
white = (255, 255, 255)
black = (0, 0, 0)
red = (255, 0, 0)
blue = (0, 0, 255)
green = (0, 255, 0)
yellow = (255, 255, 0)
skin = (222,198,174)

# Coin class
class Coin:
    def __init__(self, color, pos, vel, radius=20):
        self.color = color
        self.pos = pos
        self.vel = vel
        self.radius = radius

    def move(self):
        self.pos[0] += self.vel[0]
        self.pos[1] += self.vel[1]

    def apply_deceleration(self, deceleration_rate=0.99):
        self.vel[0] *= deceleration_rate
        self.vel[1] *= deceleration_rate

    def draw(self, screen):
        pygame.draw.circle(screen, self.color, (int(self.pos[0]), int(self.pos[1])), self.radius)

    def handle_wall_collision(self, width, height):
        if self.pos[0] - self.radius <= 0 or self.pos[0] + self.radius >= width:
            self.vel[0] = -self.vel[0]  # Reverse x velocity
        if self.pos[1] - self.radius <= 0 or self.pos[1] + self.radius >= height:
            self.vel[1] = -self.vel[1]  # Reverse y velocity

    def handle_coin_collision(self, other):
        dist = math.hypot(self.pos[0] - other.pos[0], self.pos[1] - other.pos[1])
        if dist < 2 * self.radius:
            # Calculate the normal and tangent vectors
            normal = [(other.pos[0] - self.pos[0]) / dist, (other.pos[1] - self.pos[1]) / dist]
            tangent = [-normal[1], normal[0]]
            
            # Project the velocities onto the normal and tangent vectors
            self_normal = normal[0] * self.vel[0] + normal[1] * self.vel[1]
            self_tangent = tangent[0] * self.vel[0] + tangent[1] * self.vel[1]
            other_normal = normal[0] * other.vel[0] + normal[1] * other.vel[1]
            other_tangent = tangent[0] * other.vel[0] + tangent[1] * other.vel[1]
            
            # Swap the normal components of the velocities
            new_self_normal = other_normal
            new_other_normal = self_normal
            
            # Convert the scalar normal and tangent velocities into vectors
            self.vel[0] = new_self_normal * normal[0] + self_tangent * tangent[0]
            self.vel[1] = new_self_normal * normal[1] + self_tangent * tangent[1]
            other.vel[0] = new_other_normal * normal[0] + other_tangent * tangent[0]
            other.vel[1] = new_other_normal * normal[1] + other_tangent * tangent[1]

# Create coins
coins = [
    Coin(red, [width // 3, height // 2], [2, -3]),
    Coin(blue, [2 * width // 3, height // 2], [-2, 3]),
 Coin(yellow, [width // 2, height // 3], [2, 4])
 ]

# Function to draw the carrom board
def draw_carrom_board(screen):
    # Board outline
    pygame.draw.rect(screen, white, (50, 50, width - 100, height - 100), 5)
    
    # Pockets
    pocket_radius = 30
    pockets = [
        (50, 50), (width - 50, 50),
        (50, height - 50), (width - 50, height - 50)
    ]
    for pocket in pockets:
        pygame.draw.circle(screen, black, pocket, pocket_radius)
    
    # Central circle
    pygame.draw.circle(screen, white, (width // 2, height // 2), 50, 5)
    
    # Lines and corner circles (red)
    # corner_offsets = [(100, 100), (-100, 100), (100, -100), (-100, -100)]
    # for offset in corner_offsets:
    #     end_pos = (width // 2 + offset[0], height // 2 + offset[1])
    #     pygame.draw.line(screen, white, (width // 2, height // 2), end_pos, 5)
    #     pygame.draw.circle(screen, red, end_pos, 10)

# Main game loop
clock = pygame.time.Clock()
running = True

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # Move coins
    for coin in coins:
        coin.move()

    # Handle collisions with walls
    for coin in coins:
        coin.handle_wall_collision(width, height)

    # Handle collisions between coins
    for i in range(len(coins)):
        for j in range(i + 1, len(coins)):
            coins[i].handle_coin_collision(coins[j])

    # Apply deceleration
    #for coin in coins:
        #coin.apply_deceleration()

    # Clear the screen
    screen.fill(skin)

    # Draw the carrom board
    draw_carrom_board(screen)

    # Draw coins
    for coin in coins:
        coin.draw(screen)

    # Update the display
    pygame.display.flip()

    # Cap the frame rate
    clock.tick(60)

pygame.quit()
sys.exit()

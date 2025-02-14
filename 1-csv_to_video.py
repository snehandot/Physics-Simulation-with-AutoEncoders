import pandas as pd
import pygame
import math
import sys

# Load the CSV data
df = pd.read_csv("coin_positions.csv", index_col=0)

# Initialize Pygame
pygame.init()

# Screen dimensions
width, height = 140,140
screen = pygame.display.set_mode((width, height))
pygame.display.set_caption('Replay Carrom Simulation')

# Colors
white = (255, 255, 255)
black = (0, 0, 0)
skin = (222, 198, 174)

# Font for displaying text
font = pygame.font.SysFont(None, 18)

# Coin class (simplified for replay)
class Coin:
    def __init__(self, pos, radius=10):
        self.color = white
        self.pos = pos
        self.radius = radius

    def draw(self, screen):
        pygame.draw.circle(screen, self.color, (int(self.pos[0]), int(self.pos[1])), self.radius)

# Main replay loop
clock = pygame.time.Clock()
running = True
frame_index = 0

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # Clear the screen
    screen.fill(skin)

    # Draw the carrom board
    pygame.draw.rect(screen, white, (25, 25, width - 50, height - 50), 5)

    # Get positions for the current frame
    frame_data = df.loc[frame_index].tolist()

    # Create and draw coins based on the positions
    coins = []
    for pos in frame_data:
        x, y = map(float,pos.split("--"))
        coins.append(Coin([x, y]))
        coins[-1].draw(screen)

    # Update the display
    pygame.display.flip()

    # Increment frame index
    frame_index += 1

    # Check if we've reached the end of the simulation
    if frame_index >= len(df):
        running = False

    # Cap the frame rate
    clock.tick(60)

pygame.quit()
sys.exit()

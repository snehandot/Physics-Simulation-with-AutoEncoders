import pygame
import sys
import math
import pandas as pd

pygame.init()

path="/Users/alferix/Documents/carrom/dataset/test.csv"

width, height = 200, 200
screen = pygame.display.set_mode((width, height))
pygame.display.set_caption('Carrom Simulation')

white = (255, 255, 255)
black = (0, 0, 0)
red = (255, 0, 0)
blue = (0, 0, 255)
yellow = (255, 255, 0)
skin = (222, 198, 174)

font = pygame.font.SysFont(None, 12)

collision_data = pd.DataFrame(columns=['Coin1_Pos', 'Coin2_Pos', 'Coin1_Vel_Init', 'Coin2_Vel_Init', 'Coin1_Vel_Final', 'Coin2_Vel_Final'])

class Coin:
    def __init__(self, color, pos, vel, radius=10):
        self.color = color
        self.pos = pos
        self.vel = vel
        self.radius = radius

    def move(self):
        self.pos[0] += self.vel[0]
        self.pos[1] += self.vel[1]

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
            normal = [(other.pos[0] - self.pos[0]) / dist, (other.pos[1] - self.pos[1]) / dist]
            tangent = [-normal[1], normal[0]]

            self_normal = normal[0] * self.vel[0] + normal[1] * self.vel[1]
            self_tangent = tangent[0] * self.vel[0] + tangent[1] * self.vel[1]
            other_normal = normal[0] * other.vel[0] + normal[1] * other.vel[1]
            other_tangent = tangent[0] * other.vel[0] + tangent[1] * other.vel[1]

            new_self_normal = other_normal
            new_other_normal = self_normal

            self.vel[0] = new_self_normal * normal[0] + self_tangent * tangent[0]
            self.vel[1] = new_self_normal * normal[1] + self_tangent * tangent[1]
            other.vel[0] = new_other_normal * normal[0] + other_tangent * tangent[0]
            other.vel[1] = new_other_normal * normal[1] + other_tangent * tangent[1]

            record_collision(self, other)

def record_collision(coin1, coin2):
    global collision_data
    new_data = pd.DataFrame({
        'Coin1_Pos': [(coin1.pos[0], coin1.pos[1])],
        'Coin2_Pos': [(coin2.pos[0], coin2.pos[1])],
        'Coin1_Vel_Init': [(coin1.vel[0], coin1.vel[1])],
        'Coin2_Vel_Init': [(coin2.vel[0], coin2.vel[1])],
        'Coin1_Vel_Final': [(coin1.vel[0], coin1.vel[1])],
        'Coin2_Vel_Final': [(coin2.vel[0], coin2.vel[1])]
    })
    collision_data = pd.concat([collision_data, new_data], ignore_index=True)

coins = [
    Coin(red, [width // 3, height // 2], [3, -2]),
    Coin(blue, [2 * width // 3, height // 2], [-1, 3]),
    Coin(yellow, [width // 2, height // 3], [3, 1])
]

def draw_carrom_board(screen):
    pygame.draw.rect(screen, white, (25, 25, width - 50, height - 50), 5)
    pocket_radius = 15
    pockets = [
        (25, 25), (width - 25, 25),
        (25, height - 25), (width - 25, height - 25)
    ]
    for pocket in pockets:
        pygame.draw.circle(screen, black, pocket, pocket_radius)
    pygame.draw.circle(screen, white, (width // 2, height // 2), 25, 5)

def display_coin_data(screen, coins):
    y_offset = 10
    for i, coin in enumerate(coins):
        text = f"Coin {i+1}: Pos=({int(coin.pos[0])}, {int(coin.pos[1])}) Vel=({round(coin.vel[0], 2)}, {round(coin.vel[1], 2)})"
        img = font.render(text, True, black)
        screen.blit(img, (10, y_offset))
        y_offset += 15

clock = pygame.time.Clock()
running = True

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        
        # Press 'q' to quit and view collision data
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_q:
                running = False

    for coin in coins:
        coin.move()

    for coin in coins:
        coin.handle_wall_collision(width, height)

    for i in range(len(coins)):
        for j in range(i + 1, len(coins)):
            coins[i].handle_coin_collision(coins[j])

    screen.fill(skin)
    draw_carrom_board(screen)

    for coin in coins:
        coin.draw(screen)

    display_coin_data(screen, coins)
    pygame.display.flip()
    clock.tick(60)

# After quitting the game loop, print the collision data
print(collision_data)
collision_data.to_csv(path)

pygame.quit()
sys.exit()

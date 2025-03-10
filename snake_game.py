import pygame
import time
import random
import pyttsx3
import sqlite3  # Database for storing scores
import os

# Initialize pygame
pygame.init()

# Initialize text-to-speech engine
engine = pyttsx3.init()
engine.setProperty('rate', 150)  # Speed of speech
engine.setProperty('volume', 1)  # Volume level (0.0 to 1.0)

# Database setup
db_file = "snake_game.db"

# Check if the database file exists and is not corrupted
if os.path.exists(db_file):
    try:
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='scores';")
        if cursor.fetchone() is None:
            # Table does not exist, create it
            cursor.execute('''CREATE TABLE scores 
                              (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT, score INTEGER)''')
    except sqlite3.DatabaseError:
        print("Database is corrupted. Deleting the corrupted database.")
        conn.close()
        os.remove(db_file)  # Delete the corrupted database
        # Create a new database
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()
        cursor.execute('''CREATE TABLE scores 
                          (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT, score INTEGER)''')
else:
    # Create a new database if it does not exist
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE scores 
                      (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT, score INTEGER)''')

conn.commit()

# Snake speed (default, you can change this value for different levels)
snake_speed = 15  # Default speed, adjust for difficulty

# Colors
white = (255, 255, 255)
yellow = (255, 255, 102)
black = (0, 0, 0)
red = (213, 50, 80)  # Color for the bomb
green = (0, 255, 0)
blue = (100, 200, 255)  # Lightened background for better contrast

# Display dimensions
display_width = 800
display_height = 600

display = pygame.display.set_mode((display_width, display_height))
pygame.display.set_caption('Snake Game with Sound & Leaderboard')

# Load sounds
up = pygame.mixer.Sound("GoingUp.mp3")
left = pygame.mixer.Sound("GoingLeft.mp3")
right = pygame.mixer.Sound("GoingRight.mp3")
down = pygame.mixer.Sound("GoingDown.mp3")
game_over_sound = pygame.mixer.Sound("gameover.mp3")

# Load background image
background = pygame.image.load("bg4.webp")
background = pygame.transform.scale(background, (display_width, display_height))

# Clock and snake size
clock = pygame.time.Clock()
snake_block = 20

# Font styles
font_style = pygame.font.SysFont("bahnschrift", 25)
score_font = pygame.font.SysFont("comicsansms", 35)

# Bomb variables
bomb_position = None
bomb_spawned = False

def score_display(score, username):
    value = score_font.render(f"{username} - Score: {score}", True, yellow)  # Display player name and score
    display.blit(value, [0, 0])

def draw_snake(snake_list):
    for i, pos in enumerate(snake_list):
        if i == 0:  # Head
            pygame.draw.circle(display, black, (pos[0] + 10, pos[1] + 10), 10)  # Head as a circle
        elif i == len(snake_list) - 1:  # Tail
            pygame.draw.circle(display, green, (pos[0] + 10, pos[1] + 10), 10)  # Tail as a circle
        else:  # Body
            pygame.draw.circle(display, yellow, (pos[0] + 10, pos[1] + 10), 10)  # Body as a circle

def message(msg, color):
    mesg = font_style.render(msg, True, color)
    display.blit(mesg, [display_width / 6, display_height / 3])

def get_username():
    username = ""
    input_active = True

    # Load the background image for the username input screen
    background_img = pygame.image.load("bg3.webp")  # Make sure this image exists in your folder
    background_img = pygame.transform.scale(background_img , (display_width, display_height))

    # Font for the game name and input field text
    game_name_font = pygame.font.SysFont("comicsansms", 50)
    input_text_font = pygame.font.SysFont("comicsansms", 30)

    while input_active:
        # Fill the screen with the background image
        display.blit(background_img, (0, 0))

        # Display game name at the top
        game_name = game_name_font.render("Snake Rivals", True, yellow)
        display.blit(game_name, [display_width / 3, 55])

        # Draw the input box with some padding around it
        pygame.draw.rect(display, white, (display_width / 3, display_height / 2, display_width / 3, 50))  # Input box

        # Display the typed username inside the input box
        input_text = input_text_font.render(username, True, black)
        display.blit(input_text, [display_width / 3 + 10, display_height / 2 + 10])

        # Display the prompt text above the input box (just once)
        message("Enter your username:", yellow)

        pygame.display.update()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN and username != "":
                    input_active = False  # Proceed to the game after pressing Enter
                elif event.key == pygame.K_BACKSPACE:
                    username = username[:-1]  # Remove last character
                else:
                    username += event.unicode  # Add typed character to username

    return username

def save_score(username, score):
    cursor.execute("INSERT INTO scores (username, score) VALUES (?, ?)", (username, score))
    conn.commit()

def choose_difficulty():
    global snake_speed
    difficulties = {"1": 10, "2": 15, "3": 20}  # Define speeds for Normal, Gamer, Pro Gamer
    difficulty_selected = False
    while not difficulty_selected:
        display.fill(blue)
        font = pygame.font.SysFont("comicsansms", 30)
        title = font.render("Choose Difficulty Level", True, yellow)
        display.blit(title, [display_width / 4, display_height / 5])
        message1 = font.render("1: Normal (Speed 10)", True, white)
        message2 = font.render("2: Gamer (Speed 15)", True, white)
        message3 = font.render("3: Pro Gamer (Speed 20)", True, white)
        display.blit(message1, [display_width / 3, display_height / 3])
        display.blit(message2, [display_width / 3, display_height / 2.5])
        display.blit(message3, [display_width / 3, display_height / 2])
        pygame.display.update()

        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN:
                if event.unicode in difficulties:
                    snake_speed = difficulties[event.unicode]  # Set the snake speed based on difficulty
                    return

def display_leaderboard():
    display.fill(blue)
    font = pygame.font.SysFont("comicsansms", 30)
    title = font.render("Leaderboard", True, yellow)
    display.blit(title, [display_width / 3, display_height / 10])

    cursor.execute("SELECT username, score FROM scores ORDER BY score DESC LIMIT 3")
    rows = cursor.fetchall()
    for index, (username, score) in enumerate(rows):
        score_text = font.render(f"{index + 1}. {username} - {score}", True, white)
        display.blit(score_text, [display_width / 3, display_height / 5 + index * 30])

    # Count total players
    cursor.execute("SELECT COUNT(DISTINCT username) FROM scores")
    total_players = cursor.fetchone()[0]
    total_players_text = font.render(f"Total Players: {total_players}", True, white)
    display.blit(total_players_text, [display_width / 3, display_height / 2 + 50])

    # Add options to try again or exit
    try_again_text = font.render("Press C to Try Again or Q to Quit", True, white)
    display.blit(try_again_text, [display_width / 4, display_height / 2 + 100])
    enjoy_text = font.render("Hope you enjoyed the game!", True, white)
    display.blit(enjoy_text, [display_width / 4, display_height / 2 + 150])

    pygame.display.update()
    time.sleep(5)  # Show leaderboard for 5 seconds

def spawn_bomb(score):
    global bomb_position, bomb_spawned
    if score >= 5 and (score - 5) % 2 == 0:  # Spawn bomb every 2 scores after 5
        bomb_position = (round(random.randrange(0, display_width - snake_block) / 20.0) * 20.0,
                         round(random.randrange(0, display_height - snake_block) / 20.0) * 20.0)
        bomb_spawned = True

def draw_bomb():
    if bomb_spawned:
        pygame.draw.rect(display, red, (bomb_position[0], bomb_position[1], snake_block, snake_block))  # Draw bomb as a square

def gameLoop():
    username = get_username()  # Get the username before the game starts
    choose_difficulty()  # Choose difficulty before starting the game
    game_over = False
    game_close = False

    x1 = display_width / 2
    y1 = display_height / 2

    x1_change = snake_block
    y1_change = 0

    snake_list = [[x1, y1]]
    foodx = round(random.randrange(0, display_width - snake_block) / 20.0) * 20.0
    foody = round(random.randrange(0, display_height - snake_block) / 20.0) * 20.0

    score = 0  # Initialize score

    while not game_over:
        while game_close:
            display.fill(blue)
            message("You Lost! Press Q-Quit or C-Play Again", red)
            score_display(len(snake_list) - 1, username)  # Show score with username
            pygame.display.update()

            for event in pygame.event.get():
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_q:
                        game_over = True
                        game_close = False
                    if event.key == pygame.K_c:
                        gameLoop()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                game_over = True
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_LEFT and x1_change == 0:
                    x1_change = -snake_block
                    y1_change = 0
                    pygame.mixer.Sound.play(left)
                elif event.key == pygame.K_RIGHT and x1_change == 0:
                    x1_change = snake_block
                    y1_change = 0
                    pygame.mixer.Sound.play(right)
                elif event.key == pygame.K_UP and y1_change == 0:
                    y1_change = -snake_block
                    x1_change = 0
                    pygame.mixer.Sound.play(up)
                elif event.key == pygame.K_DOWN and y1_change == 0:
                    y1_change = snake_block
                    x1_change = 0
                    pygame.mixer.Sound.play(down)

        x1 += x1_change
        y1 += y1_change

        if x1 >= display_width or x1 < 0 or y1 >= display_height or y1 < 0:
            pygame.mixer.Sound.play(game_over_sound)
            game_close = True

        if [x1, y1] in snake_list[1:]:  # Check if head collides with body (excluding the first element)
            pygame.mixer.Sound.play(game_over_sound)
            game_close = True

        if bomb_spawned and (x1, y1) == bomb_position:  # Check for collision with bomb
            pygame.mixer.Sound.play(game_over_sound)
            game_close = True

        display.blit(background, (0, 0))  # Set background image
        pygame.draw.circle(display, white, (foodx + 10, foody + 10), 10)  # Fruit

        # Add the new head to the front
        snake_list.insert(0, [x1, y1])
        if x1 == foodx and y1 == foody:
            foodx = round(random.randrange(0, display_width - snake_block) / 20.0) * 20.0
            foody = round(random.randrange(0, display_height - snake_block) / 20.0) * 20.0
            score += 1  # Increment score
        else:
            del snake_list[-1]

        draw_snake(snake_list)
        spawn_bomb(score)  # Check if bomb should spawn
        draw_bomb()  # Draw bomb if spawned
        score_display(len(snake_list) - 1, username)  # Show score with username
        pygame.display.update()

        clock.tick(snake_speed)

    save_score(username, len(snake_list) - 1)
    display_leaderboard()  # Show leaderboard after the game ends
    pygame.quit()
    quit()

# Start the game
gameLoop()

# Close the database connection when the game ends
conn.close()
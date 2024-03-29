'''spit.py
The main module that actually runs the game.
It is the only file that requires Pygame.'''
# From Python standard library
import sys

# This is not part of the standard library
import pygame

# My modules
import constants
import config
import client
import gamedata

pygame.init()

HANDS = [
    pygame.K_LEFT,
    pygame.K_RIGHT,
    pygame.K_KP0
]
PILES = [
    pygame.K_a,
    pygame.K_s,
    pygame.K_d,
    pygame.K_f,
    pygame.K_SPACE
]
CENTER_PILES = [
    pygame.K_DOWN,
    pygame.K_UP
]
OTHER = [
    pygame.K_r
]

PRESSED_CONTROLS = PILES + CENTER_PILES + OTHER

class Spit:
    '''Controls whether to display Menu or Game'''
    playing = True
    def __init__(self):
        self.running = True
        if self.running:
            Game()
        pygame.quit()
        exit()

class Screen:
    '''Creates and updates the display'''
    width = config.WINDOW_WIDTH
    height = config.WINDOW_HEIGHT
    def __init__(self):
        self.window = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption('Spit')
    def display(self, users):
        '''Displays things'''
        self.window.fill(constants.GRAY)
        for user in users:
            if users[user].ready:
                width = int(self.width / 16)
                height = width
                x_coord = int(self.width / 2 - width / 2)
                y_coord = int((abs((self.height * user) - (self.height * 7/7))) - height / 2)
                pygame.draw.rect(self.window, constants.GREEN, [x_coord, y_coord, width, height])
            cards = users[user].center_pile.cards
            if cards:
                x_coord = int(self.width / 2 - gamedata.Card.width / 2)
                y_coord = int((abs((self.height * user) - (self.height * 4/7))) - gamedata.Card.height / 2)
                card = cards[-1]
                font = pygame.font.Font('./ibm.ttf', card.font_size)
                text = card.face + card.suit
                textbox = font.render(text, True, card.color, constants.WHITE)
                pygame.draw.rect(self.window, constants.WHITE, [x_coord, y_coord, card.width, card.height])
                self.window.blit(textbox, (x_coord, y_coord))
            piles = users[user].piles
            pile_spacing = self.width / (len(piles) + 1)
            for pile in piles:
                cards = piles[pile].cards
                if cards:
                    x_coord = int((pile_spacing * (pile + 1)) - gamedata.Card.width / 2)
                    y_coord = int((abs((self.height * user) - (self.height * 5/7))) - gamedata.Card.height / 2)
                    card = cards[-1]
                    if card.flipped:
                        font = pygame.font.Font('./ibm.ttf', card.font_size)
                        text = card.face + card.suit
                        textbox = font.render(text, True, card.color, constants.WHITE)
                        pygame.draw.rect(self.window, constants.WHITE, [x_coord, y_coord, card.width, card.height])
                        self.window.blit(textbox, (x_coord, y_coord))
                    else:
                        pygame.draw.rect(
                            self.window, constants.BLUE,
                            [x_coord, y_coord, card.width, card.height]
                        )
            hands = users[user].hands
            hand_spacing = self.width / (len(hands) + 1)
            for hand in hands:
                x_coord = int(hand_spacing * (hand + 1) - gamedata.Hand.width / 2)
                y_coord = int((((abs(self.height * user - self.height)) - gamedata.Hand.height / 4) + (gamedata.Hand.height * user - gamedata.Hand.y_mod) * hands[hand].selected) - gamedata.Hand.height / 2)
                pygame.draw.rect(
                    self.window, constants.BLACK,
                    [x_coord, y_coord, gamedata.Hand.width, gamedata.Hand.height]
                )
                card = hands[hand].card
                if card:
                    text = card.face + card.suit
                    font = pygame.font.Font('./ibm.ttf', card.font_size)
                    textbox = font.render(text, True, card.color, constants.WHITE)
                    pygame.draw.rect(
                        self.window, constants.WHITE,
                        [x_coord, y_coord, card.width, card.height]
                    )
                    self.window.blit(textbox, (x_coord, y_coord))
        pygame.display.update()

class Game:
    '''Controls mechanics and high level display of the game'''
    def __init__(self):
        self.screen = Screen()
        self.networker = client.Client()
        self.deck = self.networker.deck
        self.users = gamedata.make_users(self.deck)
        self.main()
    def main(self):
        '''The main user control loop.
        Sends deck changes to the opponent.
        Calls the display of both User's elements.'''
        timer = pygame.time.Clock()

        # ALGORITHM
        #########################################################
        while True:
            # Detects hand keyholds
            for hand in range(3):
                if pygame.key.get_pressed()[HANDS[hand]]:
                    self.users[0].keys.held.append(hand)

            for event in pygame.event.get():
                # Detects pile keypresses
                if event.type == pygame.KEYDOWN:
                    for key in range(8):
                        if PRESSED_CONTROLS[key] == event.key:
                            self.users[0].keys.pressed.append(key)
        ##########################################################

                # The idea for this section was found in the official Pygame documentation
                # It detects if the user exits the window
                #############################
                # Detects quitting
                if event.type == pygame.QUIT:
                    self.networker.close()
                    pygame.quit()
                    sys.exit()
                #############################

            self.users[1].keys = self.networker.network_io(self.users[0].keys)
            for hand in self.users[0].hands:
                self.users[0].hands[hand].selected = False
            # Runs game logic/mechanics for each user
            for user in self.users:
                keys = self.users[user].keys
                if len(keys.held) == 1:
                    hand = keys.held[0]
                    if hand == 2:
                        for hand in range(2):
                            self.users[user].hands[hand].selected = True
                        hands = self.users[user].hands
                        if hands[0].card is None or hands[1].card is None:
                            if len(keys.pressed) == 1:
                                pile = keys.pressed[0]
                                self.users[user].piles[pile].cards[-1].flipped = True
                    else:
                        self.users[user].hands[hand].selected = True
                        if len(keys.pressed) == 1:
                            key = keys.pressed[0]
                            hand_card = self.users[user].hands[hand].card
                            if key in range(5):
                                pile = key
                                pile_cards = self.users[user].piles[pile].cards
                                if pile_cards:
                                    if hand_card is None:
                                        if pile_cards[-1].flipped:
                                            self.users[user].hands[hand].card = pile_cards[-1]
                                            del self.users[user].piles[pile].cards[-1]
                                    else:
                                        if pile_cards[-1].value == hand_card.value:
                                            self.users[user].piles[pile].cards.append(hand_card)
                                            self.users[user].hands[hand].card = None
                                elif self.users[user].hands[hand].card:
                                    self.users[user].piles[pile].cards.append(hand_card)
                                    self.users[user].hands[hand].card = None
                            elif hand_card:
                                if key == 5:
                                    pile_cards = self.users[user].center_pile.cards
                                    if pile_cards:
                                        value_diff = abs(pile_cards[-1].value - hand_card.value)
                                        if value_diff == 1 or value_diff == 12:
                                            self.users[user].center_pile.cards.append(hand_card)
                                            self.users[user].hands[hand].card = None
                                elif key == 6:
                                    pile_cards = self.users[int(not user)].center_pile.cards
                                    if pile_cards:
                                        value_diff = abs(pile_cards[-1].value - hand_card.value)
                                        if value_diff == 1 or value_diff == 12:
                                            self.users[int(not user)].center_pile.cards.append(hand_card)
                                            self.users[user].hands[hand].card = None
                elif len(keys.pressed) == 1:
                    key = keys.pressed[0]
                    if key == 7:
                        self.users[user].ready = not self.users[user].ready
                else:
                    for hand in self.users[user].hands:
                        self.users[user].hands[hand].selected = False
                self.users[user].keys.clear()
            if self.users[0].ready and self.users[1].ready:
                if self.users[0].deck and self.users[1].deck:
                    for user in self.users:
                        deck = self.users[user].deck
                        self.users[user].center_pile.cards.append(deck[-1])
                        del self.users[user].deck[-1]
                        self.users[user].ready = False

            self.screen.display(self.users)
            timer.tick(60)

Spit()

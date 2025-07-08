import pygame, random, sys, os

pygame.init()
WIDTH, HEIGHT = 900, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Blackjack - Split and Double")
clock = pygame.time.Clock()

FONT = pygame.font.SysFont("Arial", 24)
CARD_WIDTH, CARD_HEIGHT = 80, 120
CARD_BACK_IMAGE_PATH = "cards/back.png"

if os.path.exists(CARD_BACK_IMAGE_PATH):
    CARD_BACK = pygame.image.load(CARD_BACK_IMAGE_PATH)
    CARD_BACK = pygame.transform.scale(CARD_BACK, (CARD_WIDTH, CARD_HEIGHT))
else:
    CARD_BACK = pygame.Surface((CARD_WIDTH, CARD_HEIGHT))
    CARD_BACK.fill((30, 30, 60))
    pygame.draw.rect(CARD_BACK, (200, 200, 0), CARD_BACK.get_rect(), 4)
    txt = FONT.render("BACK", True, (255, 255, 255))
    txt_rect = txt.get_rect(center=CARD_BACK.get_rect().center)
    CARD_BACK.blit(txt, txt_rect)

SUITS = ["S", "H", "D", "C"]
RANKS = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"]
CARD_IMAGES = {}
for suit in SUITS:
    for rank in RANKS:
        card_name = f"{rank}{suit}"
        image_path = f"cards/{card_name}.png"
        if os.path.exists(image_path):
            image = pygame.image.load(image_path)
            image = pygame.transform.scale(image, (CARD_WIDTH, CARD_HEIGHT))
            CARD_IMAGES[card_name] = image
        else:
            surf = pygame.Surface((CARD_WIDTH, CARD_HEIGHT))
            surf.fill((255, 255, 255))
            pygame.draw.rect(surf, (0, 0, 0), surf.get_rect(), 2)
            txt = FONT.render(card_name, True, (0, 0, 0))
            surf.blit(txt, (10, 10))
            CARD_IMAGES[card_name] = surf

CHIP_VALUES = [25, 50, 100]
CHIP_COLORS = [(0, 200, 0), (0, 0, 255), (255, 0, 0)]

class Card:
    def __init__(self, rank, suit):
        self.rank = rank
        self.suit = suit
        self.image = CARD_IMAGES[f"{rank}{suit}"]
        self.revealed = False
        self.x, self.y = WIDTH // 2, HEIGHT // 2

    def draw(self, surf, x=None, y=None):
        draw_x = x if x is not None else self.x
        draw_y = y if y is not None else self.y
        surf.blit(self.image if self.revealed else CARD_BACK, (draw_x, draw_y))

    def value(self):
        if self.rank in ["J", "Q", "K"]:
            return 10
        if self.rank == "A":
            return 11
        return int(self.rank)

class Deck:
    def __init__(self):
        self.cards = [Card(r, s) for s in SUITS for r in RANKS]
        random.shuffle(self.cards)

    def deal(self):
        if not self.cards:
            self.cards = [Card(r, s) for s in SUITS for r in RANKS]
            random.shuffle(self.cards)
        return self.cards.pop()

class Hand:
    def __init__(self):
        self.cards = []
        self.finished = False
        self.visible = True

    def add(self, card):
        self.cards.append(card)

    def draw(self, surf, x, y):
        if self.visible:
            for i, c in enumerate(self.cards):
                c.draw(surf, x + i * (CARD_WIDTH + 10), y)

    def value(self):
        val = sum(c.value() for c in self.cards)
        aces = sum(1 for c in self.cards if c.rank == "A")
        while val > 21 and aces:
            val -= 10
            aces -= 1
        return val

    def is_pair(self):
        return len(self.cards) == 2 and self.cards[0].rank == self.cards[1].rank

class Game:
    def __init__(self):
        self.deck = Deck()
        self.player_hands = []
        self.active_hand_index = 0
        self.dealer = Hand()
        self.balance = 1000
        self.bet = 0
        self.side_bet = 0
        self.hand_bets = []
        self.message = ""
        self.screen_state = "betting"
        self.previous_screen_state = None
        self.bet_mode = None
        self.double_allowed = True
        self.split_allowed = False
        self.result_timer = 0
        self.last_winnings = 0

        # ===== ADD THIS BLOCK TO LOAD SPRITE.PNG =====
        self.sprite_image = None
        self.sprite_lose_image = None
        self.sprite_win_image = None
        self.sprite_flash_until = 0
        self.sprite_flash_type = None

        sprite_path = "Sprite/Sprite.png"
        sprite_lose_path = "Sprite/Sprite_lose.png"
        sprite_win_path = "Sprite/Sprite_win.png"

        if os.path.exists(sprite_path):
            self.sprite_image = pygame.image.load(sprite_path).convert_alpha()
            self.sprite_image = pygame.transform.scale(self.sprite_image, (200, 200))
            

        if os.path.exists(sprite_lose_path):
            self.sprite_lose_image = pygame.image.load(sprite_lose_path).convert_alpha()
            self.sprite_lose_image = pygame.transform.scale(self.sprite_lose_image, (200, 200))
            

        if os.path.exists(sprite_win_path):
            self.sprite_win_image = pygame.image.load(sprite_win_path).convert_alpha()
            self.sprite_win_image = pygame.transform.scale(self.sprite_win_image, (200, 200))
            

            
        

        self.place_bet_sound = None
        if os.path.exists("sounds/place_your_bets.wav"):
            self.place_bet_sound = pygame.mixer.Sound("sounds/place_your_bets.wav")

        # 🎵 배경음악 로드 및 반복 재생
        if os.path.exists("sounds/StandardJazzBars.wav"):
            pygame.mixer.music.load("sounds/StandardJazzBars.wav")
            pygame.mixer.music.set_volume(0.2)
            pygame.mixer.music.play(-1)

        self.win_sound = None
        self.lose_sound = None
        if os.path.exists("sounds/Youwin.wav"):
            self.win_sound = pygame.mixer.Sound("sounds/Youwin.wav")
        if os.path.exists("sounds/Youlose.wav"):
            self.lose_sound = pygame.mixer.Sound("sounds/Youlose.wav")

        self.buttons = {
            "main": pygame.Rect(50, 450, 120, 40),
            "side": pygame.Rect(200, 450, 120, 40),
            "start": pygame.Rect(350, 450, 120, 40),
            "hit": pygame.Rect(50, 500, 100, 40),
            "stand": pygame.Rect(160, 500, 100, 40),
            "double": pygame.Rect(270, 500, 100, 40),
            "split": pygame.Rect(380, 500, 100, 40),
            "reset": pygame.Rect(500, 450, 120, 40)
        }
        self.chip_rects = [pygame.Rect(100 + i * 100, 350, 60, 60) for i in range(len(CHIP_VALUES))]

    def reset(self):
        self.balance += self.bet + self.side_bet
        self.bet = 0
        self.side_bet = 0
        self.deck = Deck()
        self.player_hands = []
        self.active_hand_index = 0
        self.dealer = Hand()
        self.message = ""
        self.screen_state = "betting"
        self.bet_mode = None
        self.double_allowed = True
        self.split_allowed = False

    def start_round(self):
        self.screen_state = "playing"
        self.deck = Deck()
        self.player_hands = [Hand()]
        self.hand_bets = [self.bet]
        self.active_hand_index = 0
        self.dealer = Hand()

        card1 = self.deck.deal()
        card2 = self.deck.deal()
        card1.revealed = True
        card2.revealed = True
        card1.x, card1.y = 100, 350
        card2.x, card2.y = 190, 350
        self.player_hands[0].add(card1)
        self.player_hands[0].add(card2)

        self.deal_card(self.dealer, 100, 100, True)
        self.deal_card(self.dealer, 190, 100, False)

        self.double_allowed = True
        self.split_allowed = self.player_hands[0].is_pair() and self.balance >= self.bet
        self.resolve_side_bet()

        if self.player_hands[0].value() == 21:
            self.stand()

    def deal_card(self, hand, target_x, target_y, revealed=True):
        card = self.deck.deal()
        card.x, card.y = WIDTH // 2, HEIGHT // 2
        card.revealed = False
        hand.add(card)

        steps = 15
        dx = (target_x - card.x) / steps
        dy = (target_y - card.y) / steps

        for _ in range(steps):
            card.x += dx
            card.y += dy
            self.draw()
            pygame.display.flip()
            clock.tick(60)

        card.x, card.y = target_x, target_y
        if revealed:
            pygame.time.delay(300)
        card.revealed = revealed

    def resolve_side_bet(self):
        if self.side_bet:
            cards = self.player_hands[0].cards
            if cards[0].rank == cards[1].rank:
                win = self.side_bet * 10
                self.balance += win
                self.last_winnings = win
                self.message = "Side Bet WIN!"
            else:
                self.last_winnings = -self.side_bet
                self.message = "Side Bet LOST."
            self.side_bet = 0
        else:
            self.last_winnings = 0

    def hit(self):
        hand = self.player_hands[self.active_hand_index]
        x = 100 + self.active_hand_index * 320
        y = 350
        self.deal_card(hand, x + len(hand.cards) * (CARD_WIDTH + 10), y, True)
        self.double_allowed = False
        self.split_allowed = False

        if hand.value() == 21:
            self.stand()
        elif hand.value() > 21:
            hand.finished = True
            self.advance_hand()
    def stand(self):
        if self.active_hand_index < len(self.player_hands):
            self.player_hands[self.active_hand_index].finished = True
            self.advance_hand()

    def double(self):
        i = self.active_hand_index
        if self.balance >= self.bet:
            self.balance -= self.bet
            self.bet *= 2

            hand = self.player_hands[self.active_hand_index]
            x = 100 + self.active_hand_index * 320
            y = 350
            self.deal_card(hand, x + len(hand.cards) * (CARD_WIDTH + 10), y, True)

            self.double_allowed = False
            self.split_allowed = False

            if hand.value() > 21:
                hand.finished = True
                self.advance_hand()
            else:
                self.stand()

    def split(self):
        hand = self.player_hands[0]
        if hand.is_pair() and self.balance >= self.bet:
            self.balance -= self.bet
            new_hand1 = Hand()
            new_hand2 = Hand()
            card1, card2 = hand.cards
            new_hand1.add(card1)
            new_hand2.add(card2)
            card2.revealed = False

            self.player_hands = [new_hand1, new_hand2]
            self.hand_bets = [self.bet, self.bet]
            self.active_hand_index = 0
            self.deal_card(new_hand1, 180, 350, True)
            self.split_allowed = False
            self.double_allowed = True

    def advance_hand(self):
        self.player_hands[self.active_hand_index].visible = False
        self.active_hand_index += 1
        if self.active_hand_index < len(self.player_hands):
            for c in self.player_hands[self.active_hand_index].cards:
                c.revealed = True
            x = 100 + self.active_hand_index * 320
            y = 350
            self.deal_card(self.player_hands[self.active_hand_index], x + len(self.player_hands[self.active_hand_index].cards) * (CARD_WIDTH + 10), y, True)
        else:
            self.finish_dealer()

    def finish_dealer(self):
        for c in self.dealer.cards:
            c.revealed = True
        while self.dealer.value() < 17:
            self.deal_card(self.dealer, 100 + len(self.dealer.cards) * (CARD_WIDTH + 10), 100, True)
        self.resolve_game()

    def resolve_game(self):
        d_val = self.dealer.value()
        d_blackjack = len(self.dealer.cards) == 2 and d_val == 21

        total_result = 0

        for i, hand in enumerate(self.player_hands):
            per_hand_bet = self.hand_bets[i]
            p_val = hand.value()
            p_blackjack = len(hand.cards) == 2 and p_val == 21

            if p_blackjack and not d_blackjack:
                win = int(per_hand_bet * 1.5)
                self.balance += per_hand_bet + win
                total_result += win
                msg = "Blackjack!"
            elif p_val > 21:
                total_result -= per_hand_bet
                msg = "Bust"
            elif d_val > 21 or p_val > d_val:
                self.balance += per_hand_bet * 2
                total_result += per_hand_bet
                msg = "Win"
            elif p_val == d_val:
                self.balance += per_hand_bet
                msg = "Push"
            else:
                total_result -= per_hand_bet
                msg = "Lose"
            self.message += f"{msg} | "

        if total_result < 0:
            self.sprite_flash_until = pygame.time.get_ticks() + 1500
            self.sprite_flash_type = "lose"
        elif total_result > 0:
            self.sprite_flash_until = pygame.time.get_ticks() + 1500
            self.sprite_flash_type = "win"

        self.last_winnings += total_result
        self.bet = 0
        self.screen_state = "result"
        self.result_timer = pygame.time.get_ticks()

    def draw(self):
        screen.fill((0, 100, 0))
        screen.blit(FONT.render(f"Balance: ${self.balance}", True, (255, 255, 255)), (600, 20))
        screen.blit(FONT.render(f"Main Bet: ${self.bet}", True, (255, 255, 255)), (600, 50))
        screen.blit(FONT.render(f"Side Bet: ${self.side_bet}", True, (200, 200, 255)), (600, 80))

        lw_text = f"{self.last_winnings:+}"
        color = (255, 255, 100) if self.last_winnings >= 0 else (255, 100, 100)
        screen.blit(FONT.render(f"Last Win: ${lw_text}", True, color), (600, 110))

        if self.screen_state == "betting":
            screen.blit(FONT.render("Place Your Bets!", True, (255, 255, 0)), (50, 20))

            chip_y = HEIGHT - 140
            for i, rect in enumerate(self.chip_rects):
                x = 30 + i * 100
                chip_rect = pygame.Rect(x, chip_y, 60, 60)
                self.chip_rects[i] = chip_rect
                pygame.draw.circle(screen, CHIP_COLORS[i], chip_rect.center, 30)
                txt = FONT.render(f"${CHIP_VALUES[i]}", True, (0, 0, 0))
                screen.blit(txt, (chip_rect.x + 5, chip_rect.y + 20))

            button_y = HEIGHT - 60
            for i, name in enumerate(["main", "side", "start", "reset"]):
                x = 20 + i * 150
                self.buttons[name].x = x
                self.buttons[name].y = button_y
                color = (180, 180, 180) if self.bet_mode == name else (255, 255, 255)
                pygame.draw.rect(screen, color, self.buttons[name])
                screen.blit(FONT.render(name.upper(), True, (0, 0, 0)), (self.buttons[name].x + 10, self.buttons[name].y + 5))

        elif self.screen_state in ["playing", "result"]:
            for i, hand in enumerate(self.player_hands):
                x = 100 + i * 320
                y = 350
                hand.draw(screen, x, y)
                val_txt = FONT.render(f"Value: {hand.value()}", True, (255, 255, 255))
                screen.blit(val_txt, (x, y - 30))

            self.dealer.draw(screen, 100, 100)
            val = self.dealer.value() if self.screen_state == "result" else self.dealer.cards[0].value() if self.dealer.cards and self.dealer.cards[0].revealed else "?"
            dealer_val_text = FONT.render(f"Dealer: {val}", True, (255, 255, 255))
            screen.blit(dealer_val_text, (100, 100 + CARD_HEIGHT + 10))

            for name in ["hit", "stand"]:
                pygame.draw.rect(screen, (255, 255, 255), self.buttons[name])
                screen.blit(FONT.render(name.upper(), True, (0, 0, 0)), (self.buttons[name].x + 10, self.buttons[name].y + 5))

            if self.double_allowed:
                pygame.draw.rect(screen, (255, 255, 255), self.buttons["double"])
                screen.blit(FONT.render("DOUBLE", True, (0, 0, 0)), (self.buttons["double"].x + 5, self.buttons["double"].y + 5))
            if self.split_allowed:
                pygame.draw.rect(screen, (255, 255, 255), self.buttons["split"])
                screen.blit(FONT.render("SPLIT", True, (0, 0, 0)), (self.buttons["split"].x + 10, self.buttons["split"].y + 5))

            screen.blit(FONT.render(self.message, True, (255, 255, 0)), (50, 20))

        # === DRAW SPRITE IMAGE IF LOADED ===
        current_sprite = self.sprite_image  # 기본값

        if pygame.time.get_ticks() < self.sprite_flash_until:
            if self.sprite_flash_type == "lose" and self.sprite_lose_image:
                current_sprite = self.sprite_lose_image
            elif self.sprite_flash_type == "win" and self.sprite_win_image:
                current_sprite = self.sprite_win_image

        if current_sprite:
            screen.blit(current_sprite, (600, HEIGHT - 450))

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            pos = event.pos
            if self.screen_state == "betting":
                if self.buttons["main"].collidepoint(pos): self.bet_mode = "main"
                elif self.buttons["side"].collidepoint(pos): self.bet_mode = "side"
                elif self.buttons["start"].collidepoint(pos) and self.bet > 0: self.start_round()
                elif self.buttons["reset"].collidepoint(pos): self.reset()
                for i, rect in enumerate(self.chip_rects):
                    if rect.collidepoint(pos):
                        value = CHIP_VALUES[i]
                        if self.balance >= value:
                            if self.bet_mode == "main":
                                self.bet += value
                                self.balance -= value
                            elif self.bet_mode == "side":
                                self.side_bet += value
                                self.balance -= value
            elif self.screen_state == "playing":
                if self.buttons["hit"].collidepoint(pos): self.hit()
                elif self.buttons["stand"].collidepoint(pos): self.stand()
                elif self.double_allowed and self.buttons["double"].collidepoint(pos): self.double()
                elif self.split_allowed and self.buttons["split"].collidepoint(pos): self.split()

    def update(self):
        if self.screen_state != self.previous_screen_state:
            if self.screen_state == "betting" and self.place_bet_sound:
                self.place_bet_sound.play()
            if self.screen_state == "result":
                if self.last_winnings > 0 and self.win_sound:
                    self.win_sound.play()
                elif self.last_winnings < 0 and self.lose_sound:
                    self.lose_sound.play()
            self.previous_screen_state = self.screen_state

        if self.screen_state == "result":
            if pygame.time.get_ticks() - self.result_timer > 3000:
                self.reset()

# ===== Main Game Loop =====
game = Game()
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        game.handle_event(event)

    game.update()
    game.draw()
    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit()
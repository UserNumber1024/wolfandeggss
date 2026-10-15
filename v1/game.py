import pygame as pg
from random import randint

class Wolf(pg.sprite.Sprite):
    def __init__(self, filename):
        pg.sprite.Sprite.__init__(self)
        self.image = pg.image.load(filename).convert_alpha()
        self.update(1)

    def update(self, posit):  # установить координаты волка
        if posit == 1:
            x, y = 300, 200
        elif posit == 2:
            x, y = 500, 200
        elif posit == 3:
            x, y = 500, 350
        else:
            x, y = 300, 350

        self.rect = self.image.get_rect(center=(x, y))


class Egg(pg.sprite.Sprite):
    def __init__(self, posit, speed, filename, group):
        pg.sprite.Sprite.__init__(self)

        self.image_original = pg.image.load(filename).convert_alpha()
        self.image = self.image_original.copy()

        self.posit = posit
        self.speed = speed
        self.angle = 0

        if posit == 1:
            x, y = 50, 100
        elif posit == 2:
            x, y = 750, 100
        elif posit == 3:
            x, y = 750, 250
        else:
            x, y = 50, 250

        self.rect = self.image.get_rect(center=(x, y))
        self.add(group)

    def update(self):
        if self.posit in (1, 4):
            self.rect.x += self.speed * 2
            self.rect.y += self.speed
            self.angle -= 5
        else:
            self.rect.x -= self.speed * 2
            self.rect.y += self.speed
            self.angle += 5

        # вращаем яйцо
        self.image = pg.transform.rotate(self.image_original, self.angle)
        self.rect = self.image.get_rect(center=self.rect.center)


class Pit(pg.sprite.Sprite):
    def __init__(self, x, y, filename):
        pg.sprite.Sprite.__init__(self)
        self.image = pg.image.load(filename).convert_alpha()
        self.rect = self.image.get_rect(center=(x, y))


W_W, W_H = 800, 600          # ширина и высота окна
BACKGROUND_COLOR = "#87CEFA" # цвет фона
FPS = 30                     # количество кадров в секунду

running = True
score = 0
lives = 10
level = 1
branch = 1

# branches: номера веток (posit)
# 1 | 2
# --------
# 4 | 3

pg.init()
pg.font.init()

clock = pg.time.Clock()
pg.time.set_timer(pg.USEREVENT, 500)  # таймер появления яиц, мс

f1 = pg.font.Font(None, 50)

screen = pg.display.set_mode((W_W, W_H))
pg.display.set_caption("wolf and eggs")

wolf1 = Wolf("wolf.png")
pit1 = Pit(398, 300, "pit.png")
eggs = pg.sprite.Group()

# Основной цикл
while running:
    clock.tick(FPS)

    for e in pg.event.get():
        if e.type == pg.QUIT:
            running = False

        elif e.type == pg.KEYDOWN:
            if e.key == pg.K_ESCAPE:
                running = False

            if branch == 1:
                if e.key == pg.K_RIGHT:
                    branch = 2
                elif e.key == pg.K_DOWN:
                    branch = 4

            elif branch == 2:
                if e.key == pg.K_LEFT:
                    branch = 1
                elif e.key == pg.K_DOWN:
                    branch = 3

            elif branch == 3:
                if e.key == pg.K_LEFT:
                    branch = 4
                elif e.key == pg.K_UP:
                    branch = 2

            elif branch == 4:
                if e.key == pg.K_UP:
                    branch = 1
                elif e.key == pg.K_RIGHT:
                    branch = 3

            wolf1.update(branch)

        elif e.type == pg.USEREVENT:
            # новое яйцо появляется с вероятностью 1 к 3
            if randint(1, 3) == 1:
                Egg(
                    randint(1, 4),
                    randint(1, level),
                    "egg.png",
                    eggs
                )

    # двигаем все яйца
    eggs.update()

    # проверяем столкновения
    catch = pg.sprite.spritecollide(wolf1, eggs, True)
    lose = pg.sprite.spritecollide(pit1, eggs, True)

    if catch:
        score += 1

        if score % 10 == 0:
            level += 1

    if lose:
        lives -= 1

    # Отрисовка

    screen.fill(BACKGROUND_COLOR)

    screen.blit(wolf1.image, wolf1.rect)
    screen.blit(pit1.image, pit1.rect)

    # насесты
    pg.draw.line(screen, (150, 75, 0), [50, 120], [260, 220], 4)
    pg.draw.line(screen, (150, 75, 0), [750, 120], [520, 230], 4)
    pg.draw.line(screen, (150, 75, 0), [520, 380], [750, 270], 4)
    pg.draw.line(screen, (150, 75, 0), [50, 265], [280, 380], 4)

    # текст
    score_txt = f1.render("SCORE: " + str(score), True, (80, 10, 100))
    lives_txt = f1.render("LIVES: " + str(lives), True, (50, 80, 50))
    level_txt = f1.render("LEVEL: " + str(level), True, (180, 0, 180))
    memo_txt = f1.render("Use arrows buttons to control", True, (80, 110, 160))

    screen.blit(score_txt, (10, 10))
    screen.blit(lives_txt, (250, 10))
    screen.blit(level_txt, (480, 10))
    screen.blit(memo_txt, (150, 550))

    if lives <= 0:
        lose_txt = f1.render("YOU LOSE !!", True, (180, 10, 80))
        screen.blit(lose_txt, (300, 100))

    eggs.draw(screen)
    pg.display.update()

    # выход при проигрыше
    if lives <= 0:
        pg.time.delay(3000)
        running = False


pg.quit()
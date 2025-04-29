import os
import random
import sys
import time
import math
import pygame as pg

WIDTH = 1100
HEIGHT = 650
NUM_OF_BOMBS = 5
os.chdir(os.path.dirname(os.path.abspath(__file__)))

def check_bound(obj_rct: pg.Rect) -> tuple[bool, bool]:
    yoko, tate = True, True
    if obj_rct.left < 0 or WIDTH < obj_rct.right:
        yoko = False
    if obj_rct.top < 0 or HEIGHT < obj_rct.bottom:
        tate = False
    return yoko, tate


class Bird:
    delta = {
        pg.K_UP: (0, -5),
        pg.K_DOWN: (0, +5),
        pg.K_LEFT: (-5, 0),
        pg.K_RIGHT: (+5, 0),
    }
    img0 = pg.transform.rotozoom(pg.image.load("fig/3.png"), 0, 0.9)
    img = pg.transform.flip(img0, True, False)
    imgs = {
        (+5, 0): img,
        (+5, -5): pg.transform.rotozoom(img, 45, 0.9),
        (0, -5): pg.transform.rotozoom(img, 90, 0.9),
        (-5, -5): pg.transform.rotozoom(img0, -45, 0.9),
        (-5, 0): img0,
        (-5, +5): pg.transform.rotozoom(img0, 45, 0.9),
        (0, +5): pg.transform.rotozoom(img, -90, 0.9),
        (+5, +5): pg.transform.rotozoom(img, -45, 0.9),
    }

    def __init__(self, xy: tuple[int, int]):
        self.img = __class__.imgs[(+5, 0)]
        self.rct: pg.Rect = self.img.get_rect()
        self.rct.center = xy
        self.dire = (+5, 0)

    def change_img(self, num: int, screen: pg.Surface):
        self.img = pg.transform.rotozoom(pg.image.load(f"fig/{num}.png"), 0, 0.9)
        screen.blit(self.img, self.rct)

    def update(self, key_lst: list[bool], screen: pg.Surface):
        sum_mv = [0, 0]
        for k, mv in __class__.delta.items():
            if key_lst[k]:
                sum_mv[0] += mv[0]
                sum_mv[1] += mv[1]
        self.rct.move_ip(sum_mv)
        if check_bound(self.rct) != (True, True):
            self.rct.move_ip(-sum_mv[0], -sum_mv[1])
        if sum_mv != [0, 0]:
            self.dire = tuple(sum_mv)
            self.img = __class__.imgs[self.dire]
        screen.blit(self.img, self.rct)

class Beam:
    def __init__(self, bird: "Bird"):
        dx, dy = bird.dire
        norm = math.hypot(dx, dy)
        if norm == 0:
            norm = 1  # 安全対策（方向ベクトルが0のとき）

        speed = 5
        self.vx = dx / norm * speed
        self.vy = dy / norm * speed

        angle = math.degrees(math.atan2(-self.vy, self.vx))
        base_img = pg.image.load("fig/beam.png")
        self.img = pg.transform.rotozoom(base_img, angle, 1.0)
        self.rct = self.img.get_rect()

        bird_center = bird.rct.center
        bird_w, bird_h = bird.rct.size
        offset_x = bird_w * self.vx / 5
        offset_y = bird_h * self.vy / 5
        self.rct.centerx = bird_center[0] + offset_x
        self.rct.centery = bird_center[1] + offset_y

    def update(self, screen: pg.Surface):
        self.rct.move_ip(self.vx, self.vy)
        screen.blit(self.img, self.rct)



class Bomb:
    def __init__(self, color: tuple[int, int, int], rad: int):
        self.img = pg.Surface((2*rad, 2*rad))
        pg.draw.circle(self.img, color, (rad, rad), rad)
        self.img.set_colorkey((0, 0, 0))
        self.rct = self.img.get_rect()
        self.rct.center = random.randint(0, WIDTH), random.randint(0, HEIGHT)
        self.vx, self.vy = +5, +5

    def update(self, screen: pg.Surface):
        yoko, tate = check_bound(self.rct)
        if not yoko:
            self.vx *= -1
        if not tate:
            self.vy *= -1
        self.rct.move_ip(self.vx, self.vy)
        screen.blit(self.img, self.rct)


class Explosion:
    def __init__(self, center: tuple[int, int]):
        self.imgs = [
            pg.image.load("fig/explosion.gif"),
            pg.transform.flip(pg.image.load("fig/explosion.gif"), True, False)
        ]
        self.life = 30
        self.img = self.imgs[0]
        self.rct = self.img.get_rect()
        self.rct.center = center

    def update(self, screen: pg.Surface):
        self.life -= 1
        self.img = self.imgs[self.life // 5 % 2]
        screen.blit(self.img, self.rct)


class Score:
    def __init__(self):
        self.score = 0
        self.fonto = pg.font.SysFont("hgp創英角ﾎﾟｯﾌﾟ体", 30)
        self.color = (0, 0, 255)
        self.img = self.fonto.render(f"Score: {self.score}", 0, self.color)
        self.pos = (100, HEIGHT - 50)

    def update(self, screen: pg.Surface):
        self.img = self.fonto.render(f"Score: {self.score}", 0, self.color)
        img_rct = self.img.get_rect()
        img_rct.center = self.pos
        screen.blit(self.img, img_rct)

    def increment(self):
        self.score += 1


def main():
    pg.display.set_caption("たたかえ！こうかとん")
    screen = pg.display.set_mode((WIDTH, HEIGHT))
    bg_img = pg.image.load("fig/pg_bg.jpg")
    bird = Bird((300, 200))
    score = Score()
    beams = []
    bombs = [Bomb((255, 0, 0), 10) for _ in range(NUM_OF_BOMBS)]
    explosions = []
    clock = pg.time.Clock()
    tmr = 0

    while True:
        for event in pg.event.get():
            if event.type == pg.QUIT:
                return
            if event.type == pg.KEYDOWN and event.key == pg.K_SPACE:
                beams.append(Beam(bird))

        screen.blit(bg_img, [0, 0])

        for bomb in bombs:
            if bird.rct.colliderect(bomb.rct):
                bird.change_img(8, screen)
                fonto = pg.font.Font(None, 80)
                txt = fonto.render("Game Over", True, (255, 0, 0))
                screen.blit(txt, [WIDTH//2-150, HEIGHT//2])
                pg.display.update()
                time.sleep(1)
                return

        for beam in beams[:]:
            for bomb in bombs[:]:
                if beam.rct.colliderect(bomb.rct):
                    explosions.append(Explosion(bomb.rct.center))
                    bombs.remove(bomb)
                    beams.remove(beam)
                    bird.change_img(6, screen)
                    score.increment()
                    break

        key_lst = pg.key.get_pressed()
        bird.update(key_lst, screen)

        beams = [beam for beam in beams if 0 <= beam.rct.left <= WIDTH and 0 <= beam.rct.top <= HEIGHT]
        for beam in beams:
            beam.update(screen)

        for bomb in bombs:
            bomb.update(screen)

        explosions = [exp for exp in explosions if exp.life > 0]
        for exp in explosions:
            exp.update(screen)

        score.update(screen)
        pg.display.update()
        tmr += 1
        clock.tick(50)


if __name__ == "__main__":
    pg.init()
    main()
    pg.quit()
    sys.exit()

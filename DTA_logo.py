# Установка PIL через командную строку командой:
# pip install pillow
from PIL import Image, ImageDraw

class DTA:

    def __init__(self):
        self.WIDTH = 255
        self.HEIGHT = 177
        # transparent
        self.trns = '#ffffff00'
        self.logo = Image.new('RGBA',
                              (self.WIDTH, self.HEIGHT),
                              self.trns)
        self.draw = ImageDraw.Draw(self.logo)
        self.x = 0
        self.y = 0
        self.black = '161619'

    def save(self):
        # можно указать свой путь
        self.logo.save('DTA_logo.png')

    def show(self):
        self.logo.show()

    def makeLogo(self, letters=False):
        if letters:
            self.drawLogoWithLetters()
            self.save()
        else:
            self.drawLogoWithoutLetters()
            self.save()

    def __blueSnake(self):
        self.HEIGHT = 177
        color = '#3571A4'
        self.x = 0
        self.y = 0
        snake_width = 30
        self.draw.rectangle((self.x, self.y,
                             self.x + 60, self.y + snake_width),
                            color)
        self.draw.rectangle((self.x + 30, self.y,
                             self.x + 30 + snake_width, self.HEIGHT - 41),
                            color)
        self.draw.rectangle((self.x + 30, self.HEIGHT - 41 - snake_width,
                             self.x + 66 + snake_width, self.HEIGHT - 41),
                            color)
        self.draw.rectangle((self.x + 17, self.y + 12,
                             self.x + 25, self.y + 20),
                            self.trns)
        self.draw.line(((self.x + 25, self.y + snake_width + 1),
                        (self.x + 29, self.y + snake_width + 1),
                        (self.x + 29, self.y + snake_width + 6)),
                       color)
        self.draw.line(((self.x + 28, self.y + snake_width + 2),
                        (self.x + 28, self.y + snake_width + 4)),
                       color)
        self.draw.point((self.x + 27, self.y + snake_width + 2),
                        color)
        self.draw.line(((self.x + 31 + snake_width,
                         self.HEIGHT - 45 - snake_width),
                        (self.x + 31 + snake_width,
                         self.HEIGHT - 42 - snake_width),
                        (self.x + 34 + snake_width,
                         self.HEIGHT - 42 - snake_width)),
                       color)
        self.draw.point((self.x + 32 + snake_width,
                         self.HEIGHT - 43 - snake_width),
                        color)
        # eye
        self.draw.point(((self.x + 18, self.y + 13),
                         (self.x + 18, self.y + 19)),
                        color)
        self.__drawEyeLines([17, 19, 24, 25],
                            [15, 12, 17, 20, 13, 19],
                            color)
        # nose (head)
        self.__drawPol(self.x, self.y,
                  [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 13, 15, 17, 19, 22],
                  [24, 19, 17, 15, 13, 11, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1])
        self.__drawPol(self.x + 60, self.y,
                  [-1, -2, -3, -4, -5, -6, -7, -8, -9, -10, -11, -13, -15, -17, -19, -22],
                  [24, 19, 17, 15, 13, 11, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1])
        # tail
        self.__drawPol(self.x + 66 + snake_width,
                     self.HEIGHT - 41 - snake_width,
                  [-1, -2, -3, -4, -5, -6, -7, -8, -9, -10, -11, -13, -15, -17, -19, -22],
                  [24, 19, 17, 15, 13, 11, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1])
        self.__drawPol(self.x + 30, self.HEIGHT - 41,
                  [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 13, 15, 17, 19, 22],
                  [-24, -19, -17, -15, -13, -11, -10, -9, -8, -7, -6, -5, -4, -3, -2, -1])

    def __yellowSnake(self):
        color = '#FCD241'
        self.x = 110
        self.y = 0
        snake_width = 30
        self.HEIGHT = 165
        self.draw.rectangle((self.x, self.y,
                             self.x + snake_width, self.HEIGHT - 28),
                            color)
        self.draw.rectangle((self.x + snake_width - 2, self.HEIGHT - 57,
                             self.x + 2 * snake_width - 2, self.HEIGHT),
                            color)
        self.draw.rectangle((self.x + 41, self.HEIGHT - 25,
                             self.x + 49, self.HEIGHT - 16),
                            self.trns)
        # eye
        self.draw.point(((self.x + 42, self.HEIGHT - 24),
                         (self.x + 42, self.HEIGHT - 17),
                         (self.x + 48, self.HEIGHT - 24),
                         (self.x + 48, self.HEIGHT - 17)),
                        color)
        self.__drawEyeLines([self.x + 41, self.x + 44,
                             self.x + 47, self.x + 49],
                            [self.HEIGHT - 22, self.HEIGHT - 25,
                             self.HEIGHT - 19, self.HEIGHT - 16,
                             self.HEIGHT - 22, self.HEIGHT - 19], color)
        # body (bottom)
        self.__drawPol(self.x, self.HEIGHT - 28,
                  [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 13, 15, 17, 19, 22],
                  [-24, -19, -17, -15, -13, -11, -10, -9, -8, -7, -6, -5, -4, -3, -2, -1])
        # nose (head)
        self.__drawPol(self.x + 28, self.HEIGHT,
                  [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 13, 15, 17, 19, 22],
                  [-24, -19, -17, -15, -13, -11, -10, -9, -8, -7, -6, -5, -4, -3, -2, -1])
        self.__drawPol(self.x + 2 * snake_width - 2,
                       self.HEIGHT - 57,
                  [-1, -2, -3, -4, -5, -6, -7, -8, -9, -10, -11, -13, -15, -17, -19, -22],
                  [24, 19, 17, 15, 13, 11, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1])
        # tail
        self.__drawPol(self.x, self.y,
                  [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 13, 15, 17, 19, 22],
                  [24, 19, 17, 15, 13, 11, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1])
        # details
        self.draw.line(((self.x + snake_width - 4, self.HEIGHT - 27),
                           (self.x + snake_width - 2, self.HEIGHT - 27),
                           (self.x + snake_width - 2, self.HEIGHT - 23)),
                       color)
        self.draw.point((self.x + snake_width - 3, self.HEIGHT - 26),
                        color)
        self.draw.line(((self.x + snake_width + 1, self.HEIGHT - 61),
                        (self.x + snake_width + 1, self.HEIGHT - 58),
                        (self.x + snake_width + 3, self.HEIGHT - 58)),
                       color)
        self.draw.point((self.x + snake_width + 2, self.HEIGHT - 59),
                        color)

    def drawLogoWithoutLetters(self):
        self.WIDTH = 179
        self.HEIGHT = 165
        self.logo = self.logo.resize((self.WIDTH, self.HEIGHT), Image.ANTIALIAS)
        self.draw = ImageDraw.Draw(self.logo)
        self.__blueSnake()
        self.__yellowSnake()

    def drawLogoWithLetters(self):
        self.WIDTH = 255
        self.HEIGHT = 177
        self.logo = self.logo.resize((self.WIDTH, self.HEIGHT), Image.ANTIALIAS)
        self.draw = ImageDraw.Draw(self.logo)
        self.__blueSnake()
        self.__yellowSnake()
        self.__letters()

    def __drawPol(self, lx, ly, x, y):
        self.draw.polygon(((lx, ly + y[0]),
                           (lx, ly + y[1]),
                           (lx + x[0], ly + y[1]),
                           (lx + x[0], ly + y[2]),
                           (lx + x[1], ly + y[2]),
                           (lx + x[1], ly + y[3]),
                           (lx + x[2], ly + y[3]),
                           (lx + x[2], ly + y[4]),
                           (lx + x[3], ly + y[4]),
                           (lx + x[3], ly + y[5]),
                           (lx + x[4], ly + y[5]),
                           (lx + x[4], ly + y[6]),
                           (lx + x[5], ly + y[6]),
                           (lx + x[5], ly + y[7]),
                           (lx + x[6], ly + y[7]),
                           (lx + x[6], ly + y[8]),
                           (lx + x[7], ly + y[8]),
                           (lx + x[7], ly + y[9]),
                           (lx + x[8], ly + y[9]),
                           (lx + x[8], ly + y[10]),
                           (lx + x[9], ly + y[10]),
                           (lx + x[9], ly + y[11]),
                           (lx + x[10], ly + y[11]),
                           (lx + x[10], ly + y[12]),
                           (lx + x[11], ly + y[12]),
                           (lx + x[11], ly + y[13]),
                           (lx + x[12], ly + y[13]),
                           (lx + x[12], ly + y[14]),
                           (lx + x[13], ly + y[14]),
                           (lx + x[13], ly + y[15]),
                           (lx + x[14], ly + y[15]),
                           (lx + x[14], ly),
                           (lx + x[15], ly),
                           (lx, ly)),
                          self.trns)

    def __drawEyeLines(self, x, y, color):
        # top left
        self.draw.line(((x[0], y[0]),
                        (x[0], y[1]),
                        (x[1], y[1])),
                       color)
        # bottom left
        self.draw.line(((x[0], y[2]),
                        (x[0], y[3]),
                        (x[1], y[3])),
                       color)
        # top right
        self.draw.line(((x[2], y[1]),
                        (x[3], y[1]),
                        (x[3], y[4])),
                       color)
        # bottom  right
        self.draw.line(((x[3], y[5]),
                        (x[3], y[3]),
                        (x[2], y[3])),
                       color)

    def __letters(self):
        color = '#161619'
        # 2 snakes + 1 space in 5 px
        self.x = 146
        self.y = 38
        # letters height
        letters_h = 58
        # letter 'A'
        self.draw.rectangle((self.x, self.y,
                             self.x + 52, self.y + letters_h),
                            color)
        # clean letter 'A' (outside)
        self.__cleanLetter(self.x, self.y,
                           [24, 23, 22, 21, 20, 19, 18, 17],
                           [56, 49, 42, 35, 28, 21, 19],
                           range(0, 17),
                           range(0, 17))
        self.__cleanLetter(self.x + 52, self.y,
                           [-24, -23, -22, -21, -20, -19, -18, -17],
                           [56, 49, 42, 35, 28, 21, 19],
                           [0, -1, -2, -3, -4, -5, -6,
                            -7, -8, -9, -10, -11, -12,
                            -13, -14, -15, -16],
                           range(0, 17))
        # clean letter 'A' (inside)
        self.__cleanLetterInside(self.x + 19, self.y + 33,
                                 self.x + 9, self.y + letters_h,
                                 [1, 2, 3, 4, 5, 6, 7],
                                 [2, 3, 4, 5, 7, 8, 9,
                                  11, 13, 14, 16, 18])
        self.__cleanLetterInside(self.x + 33, self.y + 33,
                                 self.x + 43, self.y + 58,
                                 [-1, -2, -3, -4, -5, -6, -7],
                                 [2, 3, 4, 5, 7, 8, 9,
                                  11, 13, 14, 16, 18])
        self.draw.line(((self.x + 26, self.y + 15),
                        (self.x + 26, self.y + 33)),
                       self.trns)
        self.draw.rectangle((self.x + 17, self.y + 40,
                             self.x + 35, self.y + letters_h),
                            self.trns)
        # letter 'П'
        self.x = self.x + 60
        self.draw.polygon(((self.x, self.y + letters_h),
                           (self.x, self.y),
                           (self.x + 42, self.y),
                           (self.x + 42, self.y + letters_h),
                           (self.x + 34, self.y + letters_h),
                           (self.x + 34, self.y + 9),
                           (self.x + 8, self.y + 9),
                           (self.x + 8, self.y + letters_h)),
                          color)
        self.draw.point(((self.x, self.y),
                         (self.x + 42, self.y)),
                        self.trns)

    def __cleanLetterInside(self, tx, ty, bx, by, x, y):
        self.draw.polygon(((bx, by),
                           (bx, by - y[0]),
                           (bx + x[0], by - y[0]),
                           (bx + x[0], by - y[3]),
                           (bx + x[1], by - y[3]),
                           (bx + x[1], by - y[4]),
                           (bx + x[2], by - y[4]),
                           (bx + x[2], by - y[6]),
                           (bx + x[3], by - y[6]),
                           (bx + x[3], by - y[7]),
                           (bx + x[4], by - y[7]),
                           (bx + x[4], by - y[9]),
                           (bx + x[5], by - y[9]),
                           (bx + x[5], by - y[10]),
                           (bx + x[6], by - y[10]),
                           (bx + x[6], by - y[11]),
                           (bx + x[6], by)),
                          self.trns)
        self.draw.polygon(((tx, ty),
                           (tx + x[0], ty),
                           (tx + x[0], ty - y[1]),
                           (tx + x[1], ty - y[1]),
                           (tx + x[1], ty - y[3]),
                           (tx + x[2], ty - y[3]),
                           (tx + x[2], ty - y[5]),
                           (tx + x[3], ty - y[5]),
                           (tx + x[3], ty - y[7]),
                           (tx + x[4], ty - y[7]),
                           (tx + x[4], ty - y[8]),
                           (tx + x[5], ty - y[8]),
                           (tx + x[5], ty - y[10]),
                           (tx + x[5], ty)),
                          self.trns)

    def __cleanLetter(self, lx, ly, x, y, rangeX, rangeY):
        self.__clean2_3(lx, ly,
                        [x[0], x[1], x[1]], y[0],
                        [rangeX[0], rangeX[1], rangeX[2]],
                        [rangeY[0], rangeY[1], rangeY[2]])
        self.__clean2_3(lx, ly,
                        [x[2], x[2], x[2]], y[1],
                        [rangeX[3], rangeX[4], rangeX[5]],
                        [rangeY[3], rangeY[4], rangeY[5]])
        self.__clean2_3(lx, ly,
                        [x[3], x[3], x[4]], y[2],
                        [rangeX[6], rangeX[7], rangeX[8]],
                        [rangeY[6], rangeY[7], rangeY[8]])
        self.__clean2_3(lx, ly,
                        [x[4], x[5], x[5]], y[3],
                        [rangeX[9], rangeX[10], rangeX[11]],
                        [rangeY[9], rangeY[10], rangeY[11]])
        self.__clean2_3(lx, ly,
                        [x[5], x[6], x[6]], y[4],
                        [rangeX[12], rangeX[13], rangeX[14]],
                        [rangeY[12], rangeY[13], rangeY[14]])
        self.draw.line(((lx + rangeX[15], ly + y[5]),
                        (lx + rangeX[15], ly + rangeY[15]),
                        (lx + x[7], ly + rangeY[15])),
                       self.trns)
        self.draw.line(((lx + rangeX[16], ly + y[6]),
                        (lx + rangeX[16], ly + rangeY[16]),
                        (lx + x[7], ly + rangeY[16])),
                       self.trns)

    def __clean2_3(self, lx, ly, x, y, rangeX, rangeY):
        self.draw.line(((lx + rangeX[0], ly + y),
                        (lx + rangeX[0], ly + rangeY[0]),
                        (lx + x[0], ly + rangeY[0])),
                       self.trns)
        self.draw.line(((lx + rangeX[1], ly + y - 2),
                        (lx + rangeX[1], ly + rangeY[1]),
                        (lx + x[1], ly + rangeY[1])),
                       self.trns)
        self.draw.line(((lx + rangeX[2], ly + y - 5),
                        (lx + rangeX[2], ly + rangeY[2]),
                        (lx + x[2], ly + rangeY[2])),
                       self.trns)

DTA_logo = DTA()
# Можно передать параметр letters со значением true,
# чтобы получить логотип с текстом
# DTA_logo.makeLogo(letters=True)
DTA_logo.makeLogo()
DTA_logo.show()

# made by Plintus
# (Быкова С., ИКБО-20-20)

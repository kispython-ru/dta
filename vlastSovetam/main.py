# фавиконка ЦАП за авторством Лянного Андрея (ИКБО-13-20)
# для сохранения фавиконки требуется пакет PIL (pip install Pillow)
# для генерации фавиконки требуется файл graphics.py в корневой папке
# (https://mipt-cs.github.io/python3-2017-2018/extra/lab4/graphics.py)

import graphics as gr
"""
раскомментить для сохранения
from PIL import Image as NewImage
"""

window = gr.GraphWin("amogus2", 32, 32)

rect = []
rect.append([gr.Rectangle(gr.Point(0, 0), gr.Point(32, 32)), 'black'])
rect.append([gr.Rectangle(gr.Point(12, 0), gr.Point(19, 4)), 'white'])
rect.append([gr.Rectangle(gr.Point(13, 1), gr.Point(14, 2)), 'black'])
rect.append([gr.Rectangle(gr.Point(17, 1), gr.Point(18, 2)), 'black'])
rect.append([gr.Circle(gr.Point(6, 28), 4), 'green'])
rect.append([gr.Circle(gr.Point(25, 28), 4), 'green'])
rect.append([gr.Polygon(gr.Point(9, 32), gr.Point(9, 26), gr.Point(7, 23), gr.Point(24, 23),
                        gr.Point(22, 26), gr.Point(22, 32), gr.Point(20, 32), gr.Point(20, 28),
                        gr.Point(11, 28), gr.Point(11, 32)), 'blue'])
rect.append([gr.Polygon(gr.Point(0, 22), gr.Point(6, 32), gr.Point(0, 32)), 'black'])
rect.append([gr.Polygon(gr.Point(32, 22), gr.Point(26, 32), gr.Point(32, 32)), 'black'])
rect.append([gr.Polygon(gr.Point(8, 23), gr.Point(8, 18), gr.Point(11, 10), gr.Point(20, 10),
                        gr.Point(23, 18), gr.Point(23, 23)), 'blue'])
rect.append([gr.Point(7, 31), 'blue'])
rect.append([gr.Point(23, 31), 'blue'])
rect.append([gr.Polygon(gr.Point(11, 10), gr.Point(10, 5), gr.Point(20, 5), gr.Point(19, 10)),
             'blue'])
rect.append([gr.Polygon(gr.Point(11, 8), gr.Point(8, 11), gr.Point(4, 11), gr.Point(2, 13),
                        gr.Point(1, 12), gr.Point(4, 8), gr.Point(0, 10), gr.Point(0, 8), gr.Point(3, 7),
                        gr.Point(0, 5), gr.Point(5, 5), gr.Point(4, 0), gr.Point(5, 0), gr.Point(6, 4),
                        gr.Point(9, 7), gr.Point(11, 4)), 'blue'])
rect.append([gr.Polygon(gr.Point(20, 10), gr.Point(24, 11), gr.Point(28, 11), gr.Point(30, 13),
                        gr.Point(31, 12), gr.Point(28, 8), gr.Point(32, 10), gr.Point(29, 7),
                        gr.Point(32, 5), gr.Point(27, 5), gr.Point(28, 0), gr.Point(27, 0),
                        gr.Point(26, 4), gr.Point(23, 7), gr.Point(20, 7)), 'blue'])
rect.append([gr.Polygon(gr.Point(12, 7), gr.Point(13, 8), gr.Point(17, 8), gr.Point(18, 7)), 'black'])

for i in rect:
    i[0].setFill(i[1])
    i[0].setOutline(i[1])
    i[0].draw(window)

""" раскомментить для сохранения
window.postscript(file="image.eps", colormode='color')
img = NewImage.open("image.eps")
img.save("favicon.ico", "ico")
"""

window.getMouse()

window.close()

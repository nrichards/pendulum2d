# Imports
import sys;
import pygame as ge

# Starting(Initializing) the Scene
ge.init()

# Defining how fast the game should be
fps = 60
fpsClock = ge.time.Clock()

# Setting up the game display
width, height = 640, 480
screen = ge.display.set_mode((width, height))

icon = ge.image.load('placeholder.png')
ge.display.set_icon(icon)

font = ge.font.SysFont('Arial', 40)

# Time to define those Menu Buttons
objects = []


class Button():
    def __init__(self, x, y, width, height, buttonText='Button', onclickFunction=None, onePress=False):
        # Defining the button sizes
        self.x = x
        self.y = y
        self.width = width
        self.height = height

        # Defining variables for button functions
        self.onclickFunction = onclickFunction
        self.onePress = onePress

        # Defining the buttons' swaggy look
        self.fillColors = {
            'normal': '#ffffff',
            'hover': '#666666',
            'pressed': '#333333',
        }

        # Set the Buttons' size
        self.buttonSurface = ge.Surface((self.width, self.height))
        self.buttonRect = ge.Rect(self.x, self.y, self.width, self.height)

        self.buttonSurf = font.render(buttonText, True, (20, 20, 20))

        # Setting some of the variables
        self.alreadyPressed = False

        # Clearing the object so it doesn't keep getting set to the same shit
        objects.append(self)

    # Start making the button work
    def process(self):

        # Get the mouse to work
        mousePos = ge.mouse.get_pos()

        # Use those swaggy looks on our buttons
        self.buttonSurface.fill(self.fillColors['normal'])
        if self.buttonRect.collidepoint(mousePos):
            self.buttonSurface.fill(self.fillColors['hover'])

            if ge.mouse.get_pressed(num_buttons=3)[0]:
                self.buttonSurface.fill(self.fillColors['pressed'])

                # If button is pressed do thingies
                if self.onePress:
                    self.onclickFunction()


                # If not pressed, don't do crap
                elif not self.alreadyPressed:
                    self.onclickFunction()
                    self.alreadyPressed = True

            # To allow you to reclick
            else:
                self.alreadyPressed = False

        # Making sure the Buttons' Dimensions are correct
        self.buttonSurface.blit(self.buttonSurf, [
            self.buttonRect.width / 2 - self.buttonSurf.get_rect().width / 2,
            self.buttonRect.height / 2 - self.buttonSurf.get_rect().height / 2
        ])
        screen.blit(self.buttonSurface, self.buttonRect)


# Maximizing the screen
def Maximize():
    screen = ge.display.set_mode((0, 0), ge.FULLSCREEN)


# Making the button, When the button is clicked maximize the screen
maximizeButton = Button(30, 30, 400, 100, 'Maximize Screen', Maximize)

# Game Events/Quitting
while True:
    screen.fill((20, 20, 20))
    for event in ge.event.get():
        if event.type == ge.QUIT:
            ge.quit()
            sys.exit()

    for object in objects:
        object.process()

    ge.display.flip()
    fpsClock.tick(fps)

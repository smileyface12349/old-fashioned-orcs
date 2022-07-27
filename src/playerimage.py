from PIL import Image


class PlayerImage:
    """Class for managing the Images of Player Sprites and color adjusting them."""

    def __init__(self, color_tuple):  # color tuple in the following format: (r, g, b, 255)
        self.color = color_tuple  # tuple containing new color for the plyer image

    def newimage(self):
        """RBG adjust the color of the base player asset for having multiple Players in different colors"""
        img = Image.open(r"old-fashioned-orcs\assets\player_base.png")  # path to open image
        img = img.convert("RGBA")  # convert image to RGBA format

        w, h = img.size  # width, height of the image
        data = img.getdata()  # color tuples of image pixels in a list
        newdata = []  # empty list for new color tuples of image pixels
        for i in range(w * h):
            if data[i] == (0, 255, 0, 255):  # if pixel color is green
                newdata.append(self.color)
            else:
                newdata.append(data[i])

        img.putdata(newdata)  # create new player image out of given data
        img.save(r"old-fashioned-orcs\assets\player.png")  # path where the new image get saved

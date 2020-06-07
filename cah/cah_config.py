import os

from marshmallow import (Schema, fields, post_dump, post_load, pre_dump,
                         pre_load, utils, validate)
from PIL import Image, ImageDraw, ImageFont

from . import config

import re

import math

BLACK = 0
WHITE = 1

# These dimensions are in inches
DIMENSIONS = (3, 4)
TEXT_WIDTH = 2.5
FONT_SIZE = 0.25


def process(f: str):
    """
    Process a config file, and create all of the card faces for it
    """
    with open(f) as fp:
        conf = config.ConfigParser.load(fp)
    scheme = ConfigSchema()
    out = scheme.load(conf)
    out.renderAndSave(relative=os.path.dirname(f))


class Card:
    def __init__(self, text: str, t=BLACK):
        self.raw = text
        self.blanks = self.raw.count("_blank_")
        self.cardType = t
        self.color = (255, 255, 255) if t is BLACK else (0, 0, 0)
        self.background = (255, 255, 255) if t is WHITE else (0, 0, 0)
        self.image = None

    def save(self, out: str):
        """
        Save the image

        render should be called first
        """
        if self.image:
            if not os.path.exists(os.path.dirname(out)):
                os.makedirs(os.path.dirname(out))
            with open(out, "wb") as fp:
                self.image.save(fp)
                print("wrote %s" % out)

    def close(self):
        """
        Close the image
        """
        if self.image:
            self.image.close()
            self.image = None

    def render(self, xy: (int, int), textW: int, collection: Image, font: ImageFont.FreeTypeFont) -> Image:
        """
        render the card
        """

        image = Image.new(
            "RGB", xy, self.background
        )

        textImage = self.renderText(font, textW, xy[0])

        padding = (xy[0] - textImage.size[0]) // 2

        if collection:
            image.paste(
                collection,
                (padding, image.height - collection.height - padding)
            )

        if self.cardType == BLACK and self.blanks > 1:
            pickIm = self.renderPick(font)
            image.paste(pickIm, (image.width - padding - pickIm.width, image.height - padding - pickIm.height))
            pickIm.close()

        image.paste(textImage, (padding, 0))
        textImage.close()

        self.image = image

        return image

    def renderText(self, font: ImageFont.FreeTypeFont, width: int = 0, maxwidth: int = 0) -> Image:
        """
        Render the text of the card
        """
        lines = list()

        # split the words that are too long
        for match in re.finditer(r"(?:\\n|\s*)(.*?(?=\\n)|.{0,20}(?=\s|$))", self.raw):
            if match[1]:
                lines.append(match[1])

        ws, hs = zip(*[font.getsize(l) for l in lines])

        mult = 1.5

        if not width:
            width = max(ws)

        padding = (maxwidth - width) // 2


        h = round(sum(hs) / len(hs))
        height = round(h * (len(hs) - 1) * mult + hs[-1])
        im = Image.new("RGB", (width, height + padding), self.background)

        y = padding
        for l in lines:
            self.renderLine(l, im, y, h, font)
            y += round(h * mult)

        return im

    def renderLine(self, raw: str, image: Image, y: int, height: int, font: ImageFont.FreeTypeFont) -> ImageDraw:
        """
        Render a single line
        """
        # Get the number of blanks
        blanks = raw.count("_blank_")
        no_line = raw.replace("_blank_", "")
        ascent, descent = font.getmetrics()
        w, h = font.getsize(no_line)
        (width, baseline), (offset_x, offset_y) = font.font.getsize(no_line)

        if height < h:
            line = ascent
        else:
            line = height - descent / 2
            y = y - height + h


        ascent, descent = font.getmetrics()

        draw = ImageDraw.Draw(image)

        #  draw.line((0, y, w, y), fill=(255, 0, 0))
        #  draw.line((0, y + height, w, y + height), fill=(0, 255, 0))
        #  draw.line((0, y + h, w, y + h), fill=(0, 0, 255))

        if blanks > 0:
            # Get the size of each blank.

            blank_size = (image.size[0] - w) / blanks
            groups = raw.split("_blank_")

            # Render each group
            x = 0
            for group in groups:
                # Draw the text
                draw.text((x, y), group, self.color, font)

                w, _ = font.getsize(group)
                x += w

                if blanks > 0:
                    # Draw the line
                    draw.line((
                        (x + 5, y + line),
                        (x + blank_size - 5, y + line)
                    ), fill=self.color, width=2)

                    x += blank_size
                    blanks -= 1
            return
        draw.text((0, y), raw, self.color, font)

    def renderCircle(self, txt: str, font: ImageFont.FreeTypeFont) -> Image:
        """
        Render text inside a circle
        """
        txt = str(txt)

        # Get the size of the circle
        w, h = font.getsize(txt)
        diam = round(math.sqrt(w ** 2 + h ** 2) * 1.25)

        im = Image.new("RGB", (diam, diam), (0, 0, 0))
        draw = ImageDraw.Draw(im)

        draw.ellipse((0, 0, diam, diam), fill=(255, 255, 255))
        draw.text((diam//2 - w//2, diam//2 - h//2), txt, fill=(0, 0, 0), font=font)

        return im

    def renderPick(self, font: ImageFont.FreeTypeFont) -> Image:
        """
        Render Pick 2, or draw 2/pick 3
        """

        # Figure out the size of the image
        pickIm = self.renderCircle(self.blanks, font)
        w, h = pickIm.size

        pickT = "PICK "
        pw, ph = font.getsize(pickT)
        w += pw

        if self.blanks > 2:
            h = round(h * 1.75)

            drawIm = self.renderCircle(self.blanks - 1, font)
            drawT = "DRAW "
            dw, dh = font.getsize(drawT)
            h += dh

            w = max(w, drawIm.width + dw)
        else:
            drawIm = None

        im = Image.new("RGB", (w, h), (0, 0, 0))
        draw = ImageDraw.Draw(im)

        # Draw the Pick
        nw, nh = pickIm.size
        im.paste(pickIm, (w - nw, h - nh))
        draw.text((w - nw - pw, h - nh // 2 - ph // 2), pickT, fill=(255, 255, 255), font=font)

        if drawIm:
            # Draw the Draw
            nw, nh = drawIm.size
            im.paste(drawIm, (w - nw, 0))
            draw.text((w - nw - dw, nh // 2 - dh // 2), drawT, fill=(255, 255, 255), font=font)

        # Close the temporary images
        pickIm.close()
        if drawIm:
            drawIm.close()

        newIm = im.resize((round(w * 0.75), round(h * 0.75)), resample=Image.LANCZOS)
        im.close()

        return newIm

    def __str__(self):
        return self.raw.replace("\\n", "\n")

    def __repr__(self):
        return "<Card(text='{}')>".format(self.raw)


class Group:
    def __init__(self, collection: str, collection_scale: float, items: list, cardType: int):
        self.collection = collection
        self.items = list()
        for item in items:
            if isinstance(item, Card):
                self.items.append(item)
                continue
            self.items.append(Card(item, cardType))
        self.cardType = cardType
        self.collection_scale = collection_scale

    def renderAndSave(self, xy: (int, int), textW: int, font: ImageFont.FreeTypeFont, out: str, relative=""):
        """
        Render and save all of the cards in this group
        """
        collection = os.path.join(relative, self.collection) if not os.path.isabs(self.collection) else self.collection

        if self.collection:
            collectionImage = Image.open(collection)

            w, h = collectionImage.size

            nw = round(textW * self.collection_scale)

            asp = nw / w
            nh = round(asp * h)

            col = collectionImage.resize((nw, nh))
            collectionImage.close()
            collectionImage = None
        else:
            col = None

        for i, card in enumerate(self.items):
            card.render(xy, textW, col, font)
            card.save(out % ("black" if self.cardType == BLACK else "white", i))
            card.close()

        if self.collection:
            col.close()

    def __repr__(self):
        return "<Group(cardType={}, collection='{}', items={})>".format(
            "BLACK" if self.cardType == BLACK else "WHITE",
            self.collection, len(self.items)
        )


class Config:
    def __init__(self, black: Group, white: Group, out: str, font: str, dpi: int):
        self.black = black
        self.white = white
        self.out = out
        self.font = font
        self.dpi = dpi

    def renderAndSave(self, dpi: float = 160, relative: str=""):
        """
        Render and Save all black and white cards
        """
        xy = tuple(round(i * dpi) for i in DIMENSIONS)
        textW = round(TEXT_WIDTH * dpi)

        relfont = os.path.join(relative, self.font) if not os.path.isabs(self.font) else self.font
        rel = os.path.join(relative, self.out) if not os.path.isabs(self.out) else self.out

        font = ImageFont.FreeTypeFont(relfont, round(FONT_SIZE * dpi))

        self.black.renderAndSave(xy, textW, font, rel, relative=relative)
        self.white.renderAndSave(xy, textW, font, rel, relative=relative)

    def __repr__(self):
        return "<Config(black={}, white={})>".format(
            self.black,
            self.white
        )


########################
#
# Schemas
#
########################


class GroupSchema(Schema):
    items = fields.List(fields.String())
    collection = fields.String(allow_none=True)
    collection_scale = fields.Float()

    def __init__(self, cardType: int, **kwargs):
        super().__init__(**kwargs)
        self.cardType = cardType

    @pre_load
    def setupGroup(self, data: dict, **kwargs):
        return {
            "items": data.get("default"),
            "collection": data.get("collection"),
            "collection_scale": data.get("collection_scale", 1)
        }

    @post_dump
    def dumpGroup(self, data: dict, **kwargs):
        return {
            "default": data.get("items"),
            "collection": data.get("collection"),
            "collection_scale": data.get("collection_scale")
        }

    @pre_dump
    def dumpCards(self, data, **kwargs):
        def getString(obj):
            if isinstance(obj, str):
                return obj
            return utils.get_value(obj, "raw")

        return {
            "items": list(map(getString, utils.get_value(data, "items"))),
            "collection": utils.get_value(data, "collection"),
            "collection_scale": utils.get_value(data, "collection_scale")
        }

    @post_load
    def loadGroup(self, data: dict, **kwargs):
        return Group(
            cardType=self.cardType,
            **data
        )


class ConfigSchema(Schema):
    black = fields.Nested(GroupSchema(BLACK))
    white = fields.Nested(GroupSchema(WHITE))
    out = fields.String()
    font = fields.String()
    dpi = fields.Integer()

    @pre_load
    def setupConfig(self, data: dict, **kwargs):
        default = data.get("default", dict())
        return {
            "black": data.get("black"),
            "white": data.get("white"),
            "out": default.get("out", "out/%s/%d.png"),
            "font": default.get("font", "Helvetica_Neue_75.otf"),
            "dpi": default.get("dpi", 160)
        }

    @post_load
    def loadConfig(self, data, **kwargs):
        return Config(**data)

    @post_dump
    def dumpConfig(self, data: dict, **kwargs):
        return {
            "black": data.get("black"),
            "white": data.get("white"),
            "default": {
                "out": data.get("out"),
                "font": data.get("font"),
                "dpi": data.get("dpi")
            }
        }

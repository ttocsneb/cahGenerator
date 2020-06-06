import os

from marshmallow import (Schema, fields, post_dump, post_load, pre_dump,
                         pre_load, utils, validate)
from PIL import Image, ImageDraw, ImageFont

from . import config

import re

BLACK = 0
WHITE = 1

DIMENSIONS = (3, 4)
TEXT_WIDTH = 2.5
FONT_SIZE = 0.25


def load(f: str):
    conf = config.ConfigParser()
    with open(f) as fp:
        conf.load(fp)
    scheme = ConfigSchema()
    out = scheme.load(conf.data)
    out.renderAndSave()


class Card:
    def __init__(self, text: str, t=BLACK):
        self.raw = text
        self.blanks = self.raw.count("_blank_")
        self.cardType = t
        self.color = (255, 255, 255) if t is BLACK else (0, 0, 0)
        self.background = (255, 255, 255) if t is WHITE else (0, 0, 0)
        self.image = None

    def save(self, out: str):
        if self.image:
            if not os.path.exists(os.path.dirname(out)):
                os.makedirs(os.path.dirname(out))
            with open(out, "wb") as fp:
                self.image.save(fp)
                print("wrote %s" % out)

    def close(self):
        if self.image:
            self.image.close()
            self.image = None

    def render(self, xy: (int, int), textW: int, collection: Image, font: ImageFont.FreeTypeFont) -> Image:

        image = Image.new(
            "RGB", xy, self.background
        )

        textImage = self.renderText(font, textW)

        padding = (xy[0] - textImage.size[0]) // 2

        image.paste(textImage, (padding, padding))

        self.image = image
        textImage.close()

        image.paste(
            collection,
            (padding, image.height - collection.height - padding)
        )

        return image

    def renderText(self, font: ImageFont.FreeTypeFont, width: int = 0) -> Image:
        # Convert raw text into list of lines

        # This soup
        # tastes like _blank_.
        lines = list()

        # split the words that are too long
        for match in re.finditer(r"(?:\\n|\s*)(.*?(?=\\n)|.{0,20}(?=\s|$))", self.raw):
            lines.append(match[1])

        ws, hs = zip(*[font.getsize(l) for l in lines])

        mult = 1.5

        if not width:
            width = max(ws)

        im = Image.new("RGB", (width, int(sum(hs) * mult)), self.background)

        y = 0
        for h, l in zip(hs, lines):
            self.renderLine(l, im, y, font)
            y += int(h * mult)

        return im

    def renderLine(self, raw: str, image: Image, y: int, font: ImageFont.FreeTypeFont) -> ImageDraw:
        # Get the number of blanks
        blanks = raw.count("_blank_")
        no_line = raw.replace("_blank_", "")
        ascent, descent = font.getmetrics()
        w, h = font.getsize(no_line)

        draw = ImageDraw.Draw(image)

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
                        (x + 5, y + h),
                        (x + blank_size - 5, y + h)
                    ), fill=self.color, width=2)

                    x += blank_size
                    blanks -= 1
            return
        draw.text((0, y), raw, self.color, font)

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
        self.collectionImage = None
        self.collection_scale = collection_scale

    def loadCollection(self) -> Image:
        self.collectionImage = Image.open(self.collection)
        return self.collectionImage

    def renderAndSave(self, xy: (int, int), textW: int, font: ImageFont.FreeTypeFont, out: str):

        if not self.collectionImage:
            self.loadCollection()

        w, h = self.collectionImage.size

        nw = round(textW * self.collection_scale)

        asp = nw / w
        nh = round(asp * h)

        col = self.collectionImage.resize((nw, nh))
        self.collectionImage.close()
        self.collectionImage = None

        for i, card in enumerate(self.items):
            card.render(xy, textW, col, font)
            card.save(out % ("black" if self.cardType == BLACK else "white", i))
            card.close()

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

    def renderAndSave(self, dpi: float = 160):
        xy = tuple(round(i * dpi) for i in DIMENSIONS)
        textW = round(TEXT_WIDTH * dpi)

        font = ImageFont.FreeTypeFont(self.font, round(FONT_SIZE * dpi))

        self.black.renderAndSave(xy, textW, font, self.out)
        self.white.renderAndSave(xy, textW, font, self.out)

    def __repr__(self):
        return "<Config(black={}, white={})>".format(
            self.black,
            self.white
        )


class GroupSchema(Schema):
    items = fields.List(fields.String())
    collection = fields.String()
    collection_scale = fields.Float()

    def __init__(self, cardType: int, **kwargs):
        super().__init__(**kwargs)
        self.cardType = cardType

    @pre_load
    def setupGroup(self, data: dict, **kwargs):
        return {
            "items": data.get("default"),
            "collection": data.get("collection"),
            "collection_scale": data.get("collection_scale")
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
    out = fields.String(missing="out/%s/%d.png")
    font = fields.String(required=True)
    dpi = fields.Integer(missing=160)

    @pre_load
    def setupConfig(self, data: dict, **kwargs):
        default = data.get("default", dict())
        return {
            "black": data.get("black"),
            "white": data.get("white"),
            "out": default.get("out"),
            "font": default.get("font"),
            "dpi": default.get("dpi")
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

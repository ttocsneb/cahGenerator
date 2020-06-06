# CAH Generator

> Cards Against Humanity Generator

Generates faces for the game Cards Against Humanity.

---

## Installation

This requires python > 3.5 as well as [pillow](https://pypi.org/project/Pillow/)
and [marshmallow](https://pypi.org/project/marshmallow/) to work.

To install simply run `pip install -r requirements.txt` or if you are using
[pipenv](https://pypi.org/project/pipenv/): `pipenv install`

## Usage

### Config

To create your own cards, you need to create a configuration file. These
files are a modified version of .ini files. This configuration will allow you
to create new cards, specifying the location where they will be saved, what
font to use, and what collection image to use.

```ini
out = asdf/%s/%02d.png ; The format of the generated cards
font = Helvetica_Neue_75.otf ; The font to use
dpi = 160 ; The size of the card

[black]
; All black cards are stored here

; The collection image is placed at the bottom of the card to let you know
; Where that card came from
collection = collections/asdf_black.png ; The image to use for the collection
collection_scale = 0.5 ; How big should the image be

; Each card is on its own line with no = sign!
Why am I like this?

; Black cards can have a blank which is represented by _blank_
That moment when _blank_.

[white]
; All white cards are stored here

collection = collections/asdf_white.png
collection_scale = 0.5

The moment Jeff walked into the bar
```

You can see `food.ini` for a better example of what the config file should look
like

### Running

To process the config file, you can run the module with the file(s) as a
parameter.

```bash
python3 -m cah asdf.ini
```

## TODO

### Pick 2

If a black card has two or more blanks, It should show in the bottom right
corner of the card.

![Pick 2 Example](https://thefictionals.com/wp-content/uploads/2014/05/images_iah-example-1.jpg)

If there are 3 blanks, the message should be draw 2 and pick 3.

I don't know what the message should be if there are more than 3 blanks, but if
there were more than 3 blanks, I don't think people would like it.

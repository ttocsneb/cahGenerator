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
; The format of the generated card files
; The parameters are:
;   %s: either black or white
;   %d: file number
;   If collating:
;     %d: number of cards
out = out/%s/asdf-%d-%d.png ; The format of the generated cards
font = Helvetica_Neue_75.otf ; The font to use
dpi = 133 ; The size of the card (default: 133)
collate = yes; whether t collate or not (default: no)

[black]
; All black cards are stored here

; The collection image is placed at the bottom of the card to let you know
; Where that card came from
collection = collections/asdf_black.png ; The image to use for the collection (optional)
collection_scale = 0.5 ; How big should the image be (default: 1)

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

You can see `cards/ama.ini` for a better example of what the config file should look
like

### Running

To process the config file, you can run the module with the file(s) as a
parameter.

```bash
python3 -m cah asdf.ini
```

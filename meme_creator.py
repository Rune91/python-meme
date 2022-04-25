import requests
import re
import json
import PIL.Image
import PIL.ImageFont
import PIL.ImageDraw
from io import BytesIO
import os.path

class MemeCreator:
    
    def __init__(self):
        self.WIDTH = 400
        self.HEIGHT = 300
        self.X_MARGIN = int(self.WIDTH / 30)
        self.Y_MARGIN = int(self.HEIGHT / 15)
        self.HEIGHT_COEFF = 1.1
        self.font_color = (255,255,255)
        self.outline_color = (0,0,0)
        self.font_name = "unicode-impact.ttf"
        if not os.path.exists(self.font_name):
            raise Exception(f"font file {self.font_name} missing from directory")
        self.watermark = "github.com/Rune91/python-meme"

    def search_image(self, keyword):
        """returns a PIL image found by searching duckduckgo for keywords"""
        image_url = self.get_image_url(keyword)
        r = requests.get(image_url)
        img = PIL.Image.open(BytesIO(r.content))
        return img
    
    def get_image_url(self, keywords):
        """returns the url to an image found by searching duckduckgo for keywords.
        Inspired by https://github.com/deepanprabhu/duckduckgo-images-api"""
        url = 'https://duckduckgo.com/';
        params = {
        	'q': keywords
        }
        res = requests.post(url, data=params)
        searchObj = re.search(r'vqd=([\d-]+)\&', res.text, re.M|re.I)
        if not searchObj:
            print("No token")
            return
        token = searchObj.group(1)
        headers = {
            'authority': 'duckduckgo.com',
            'accept': 'application/json, text/javascript, */*; q=0.01',
            'sec-fetch-dest': 'empty',
            'x-requested-with': 'XMLHttpRequest',
            'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.163 Safari/537.36',
            'sec-fetch-site': 'same-origin',
            'sec-fetch-mode': 'cors',
            'referer': 'https://duckduckgo.com/',
            'accept-language': 'en-US,en;q=0.9',
        }
        params = (
            ('l', 'us-en'),
            ('o', 'json'),
            ('q', keywords),
            ('vqd', token),
            ('f', ',,,'),
            ('p', '1'),
            ('v7exp', 'a'),
        )
        requestUrl = url + "i.js"
        try:
            res = requests.get(requestUrl, headers=headers, params=params)
            data = json.loads(res.text)
        except ValueError as e:
            print("Error fetching JSON: " + e)
        all_results = data["results"]
        if len(all_results) > 0:
            first = all_results[0]
            image_url = first["image"]
            return image_url
        else:
            if " " in keywords:
                word_list = keywords.split(" ")
                word_list.sort(key=len)
                keywords = word_list[:-1] # remove the longest word
                return self.get_image_url(keywords)
            else:
                return self.get_image_url("question mark")
            
    def draw_watermark(self, image):
        """Adds the watermark text to bottom left. Returns updated image"""
        if not self.watermark: return image
        font = PIL.ImageFont.truetype(self.font_name, 10)
        draw = PIL.ImageDraw.Draw(image)
        draw.text((2, self.HEIGHT-15), self.watermark,
                  font=font,
                  fill=self.font_color,
                  stroke_fill=self.outline_color,
                  stroke_width=1)
        
        return image
            
    def draw_text(self, text, image, top):
        """draws text on the image. top (True/False) decides top or bottom.
        returns the new image"""
        if not text: return image
        font_size = self.get_font_size(text)
        font = PIL.ImageFont.truetype(self.font_name, font_size)
        draw = PIL.ImageDraw.Draw(image)
        outline_width = int(font_size / 10)
        lines = []
        words = text.split(" ")
        draw_text = ""
        for (i, word) in enumerate(words):
            draw_text += word + " "
            if not i == len(words)-1:
                w, h = font.getsize(draw_text + words[i+1])
            else:
                w, h = 0, 0
            if i == len(words)-1 or w > self.WIDTH-2*self.X_MARGIN:
                w, h = font.getsize(draw_text)
                x = int((self.WIDTH-2*self.X_MARGIN-w) / 2 + self.X_MARGIN)
                draw_text = draw_text[:-1]
                lines.append([x, draw_text])
                draw_text = ""
        y = self.Y_MARGIN if top else self.HEIGHT-self.Y_MARGIN
        dy = 1 if top else -1
        if not top:
            lines.reverse()
            y -= int(h*self.HEIGHT_COEFF)
        for line in lines:
            x, line_text = line
            draw.text((x, y),
                          line_text,
                          font=font,
                          fill=self.font_color,
                          stroke_fill=self.outline_color,
                          stroke_width=outline_width)
            y += int(dy*h*self.HEIGHT_COEFF)
        return image

    def get_font_size(self, text):
        """returns the font size needed to draw this text on the image"""
        letters = len(text)
        while True:
            letter_width = (self.WIDTH-2*self.X_MARGIN) / (letters+2)
            if letter_width < self.WIDTH / 15:
                letters /= 2
            else:
                return int(letter_width)

    def make(self, img_keywords, text_top="", text_bottom=""):
        """searches for the image keywords. Draws text.
        Returns the completed PIL image"""
        image = self.search_image(img_keywords)
        image = image.convert("RGB")
        image = image.resize((self.WIDTH, self.HEIGHT), PIL.Image.LANCZOS)
        image = self.draw_text(text_top, image, True)
        image = self.draw_text(text_bottom, image, False)
        image = self.draw_watermark(image)
        return image


if __name__ == '__main__':
    meme_creator = MemeCreator()
    image_keywords = "chemistry"
    top_text = "Can you tell me the symbol for sodium?"
    bottom_text = "Na"
    meme = meme_creator.make(image_keywords, top_text, bottom_text)
    meme.show()
    meme.save("my_meme.png", "PNG")
import os
import re
import argparse
import pygame
from datetime import datetime
from PIL import Image

parser = argparse.ArgumentParser()
parser.add_argument("sprite_folder", help="Directory that contain all 8x8 sprites")
parser.add_argument("x", help="honrizontal size of the map", type=int)
parser.add_argument("y", help="vertical size of the map", type=int)

FILE_REGEX = re.compile(r"([sn])(\d\d?)(.*)")

palettes = []

class Tile:
    def __init__(self, file):
        with open(file, 'rb') as fd:
            img = Image.open(fd)
            if img.size != (8, 8):
                raise Exception(f"File {file} incorrect : Sprites must be 8x8 file")
            self.pil_img = img
            self.pyg_image = pygame.image.fromstring(img.tobytes(), img.size, img.mode)
        self.file_name = file
        self.name_no_ex = file.split('.', 1)[0]
        self.pal_file_name = self.name_no_ex + '.pal'
        self.name = self.name_no_ex.rsplit('/', 1)[1]
        match = FILE_REGEX.match(self.name)
        if not match:
            raise Exception(f"File named \"{self.name}\" must match regular expression {FILE_REGEX.pattern}")
        self.is_solid = match[1] == 's'
        self.id = int(match[2])
        if self.id not in range(0, 16):
            raise Exception(f"Image ID must be between 0 and 15, but it was {self.id}")
        self.description = match[3]
        tmp_pal = Palette(self.pal_file_name)
        if tmp_pal not in palettes:
            palettes.append(tmp_pal)
            if len(palettes) > 8:
                raise Exception("Too many palette, you can't have more than 8")
        self.pal_id = palettes.index(tmp_pal)


    def to_byte(self):
        return ((self.pal_id << 5) + (self.is_solid << 4) + self.id).to_bytes(1, "big")


class Palette:
    def __init__(self, file):
        with open(file, 'rb') as fd:
            self.bytes = fd.read()

    def __eq__(self, other):
        return self.bytes != other.bytes



class Map:
    def __init__(self, x : int, y : int, default_tile):
        self.size_x = x
        self.size_y = y
        self.size = (x, y)
        self.total_size = x * y
        self.tiles = [default_tile for i in range(self.total_size)]

    def __setitem__(self, key, value):
        if isinstance(key, tuple):
            self.tiles[key[0] + key[1] * self.size_x] = value
        else:
            raise TypeError("Map.__setitem__ key must be a tuple")

    def __getitem__(self, key):
        if isinstance(key, tuple):
            return self.tiles[key[0] + key[1] * self.size_x]
        else:
            raise TypeError("Map.__setitem__ key must be a tuple")

    def to_bytes(self):
        return (self.total_size.to_bytes(2, "big") + self.size_x.to_bytes(1, "big") + self.size_y.to_bytes(1, "big")
                + b''.join([p.bytes for p in palettes]) + b'\x00' * 8 * (8 - len(palettes)) + b''.join([i.to_byte() for i in self.tiles])
                )


def main(args):
    sprites = [Tile(f"{args.sprite_folder}/{i}") for i in os.listdir(args.sprite_folder) if i.endswith('.png')]
    #if len(sprites) != palettes:
    #    raise Exception(f"You must have the same number of sprites and palettes, found {sprites} sprites and {palettes} palettes")

    pygame.init()
     # scale_ratio = 1000 //  max(args.x, args.y)
    window_surface = pygame.display.set_mode((args.x * 8, args.y * 8), flags=pygame.RESIZABLE)

    surface = pygame.Surface((args.x * 8, args.y * 8))
    for i in range(args.x):
        for j in range(args.y):
            surface.blit(sprites[0].pyg_image, (i * 8, j * 8))

    game_map = Map(args.x, args.y, sprites[0])
    selected = 0

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    selected = (selected - 1) % len(sprites)
                    print(f"Selected {sprites[selected].name}")
                if event.key == pygame.K_DOWN:
                    selected = (selected + 1) % len(sprites)
                    print(f"Selected {sprites[selected].name}")
                if event.key == pygame.K_s:
                    with open(datetime.now().strftime("Map_%Y_%m_%d__%H_%M_%S"), 'wb') as fd:
                        fd.write(game_map.to_bytes())
            if event.type == pygame.VIDEORESIZE:
                ...
                window_surface = pygame.display.set_mode((event.w, event.h),pygame.RESIZABLE)

            if event.type == pygame.MOUSEBUTTONUP:
                clickx, clicky = pygame.mouse.get_pos()
                real_x = int(clickx / window_surface.get_size()[0] * game_map.size_x)
                real_y = int(clicky / window_surface.get_size()[1] * game_map.size_y)
                game_map[real_x, real_y] = sprites[selected]
                surface.blit(sprites[selected].pyg_image, (real_x * 8, real_y * 8))

        pygame.transform.scale(surface, window_surface.get_size(), window_surface)
        pygame.display.flip()





main(parser.parse_args())
'''Utils'''

import io
import math

from colour import Color
from PIL import Image, ImageDraw

import numpy as np
from scipy.interpolate import griddata


def constrain(val, min_val, max_val):
  return min(max_val, max(min_val, val))


def map_value(x, in_min, in_max, out_min, out_max):
  return (x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min


def interpolate_image(pixels, image_width, image_height, min_temperature, max_temperature,
  color_cold, color_hot, color_depth, method, rotate, mirror, format):

  rows = pixels.shape[0]
  cols = pixels.shape[1]
  
  pixels = pixels.astype(np.float)

  if rotate == 180:
    pixels = np.flip(pixels, 0)

  if mirror:
    pixels = np.flip(pixels, 1)

  pixels = [map_value(p, min_temperature, max_temperature, 0, color_depth - 1) for p in pixels.flatten()]
  
  points = [(math.floor(ix / rows), (ix % cols)) for ix in range(0, rows*cols)]
  grid_x, grid_y = np.mgrid[0:rows-1:32j, 0:cols-1:32j]

  # Create the array of colors
  colors = list(Color(color_cold).range_to(Color(color_hot), color_depth))
  colors = [(int(c.red * 255), int(c.green * 255), int(c.blue * 255)) for c in colors]

  pixel_width = image_width / 32
  pixel_height = image_width / 32

  # Perform interpolation
  interpolation = griddata(points, pixels, (grid_x, grid_y), method=method)

  image = Image.new("RGB", (image_width, image_height))
  draw = ImageDraw.Draw(image)

  for y, row in enumerate(interpolation):
    for x, pixel in enumerate(row):
      color_index = constrain(int(pixel), 0, color_depth - 1)
      x0 = pixel_width * x
      y0 = pixel_height * y
      x1 = x0 + pixel_width
      y1 = y0 + pixel_height
      draw.rectangle(((x0, y0), (x1, y1)), fill=colors[color_index])
      #draw.text((x0, y0), str(int(pxl / (COLORDEPTH / (MAXTEMP - MINTEMP)))))

  with io.BytesIO() as output:
    if format is "JPEG":
      image.save(output, format=format, quality=80, optimize=True, progressive=True)
    else:
      image.save(output, format=format)
    return output.getvalue()        
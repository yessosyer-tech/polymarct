TICK // THE POLYMARCT MASCOT

Who he is
  TICK is the acid bar from the mark, stood up and given a face.
  A tick is the smallest move a price can make, and in the logo that bar
  IS the last price, standing in the gap between the two sides of the book.
  That is the whole idea: he is the price, so he can explain the price.
  At the end of his film he climbs back into the gap and becomes the bar.

Files here
  One image is one thing. There is no sheet and no grid of thumbnails.

  pose-01-idle.png  ... pose-10-split.png    one pose per image, 1200x1200
  cutout-idle.png   ... cutout-split.png     the same poses, no background
  01-what-the-number-means.png  67c buys a dollar if it happens
  02-why-it-moves.png           the price moves when somebody knows first
  03-what-you-are-buying.png    shares, not a bet slip
  04-reality-decides.png        a named source, read at a named time

His film
  dist/polymarct-05-tick-1080p.mp4   24 seconds, 1080p30, with score

Rules, do not break them
  He is acid green. The visor is graphite, the eyes and arms are warm white,
  the data dot on his tape is electric blue. No other colours, ever.
  He floats. He has no legs.
  He never covers the number he is pointing at. Point beside it, not on it.
  He points with the dashed acid line, never with a drawn arrow.
  He does not talk in first person and he does not promise anything.
  He is used to explain, not to sell.

How he is drawn
  One Python function draws him everywhere, so he cannot drift:

    python tools/tick_poses.py     one image per pose, plus the cutouts
    python tools/tick_cards.py     the four explainer cards
    python tools/tick_film.py      the film, straight to MP4

  tools/tick.py is the character itself:

    tick.draw(img, x, y, s, pose, dir, expr, label, t)  -> hand position
    tick.pointer(img, hand, target)                     -> the dashed line

  Poses: idle, point, think, cheer, hold, press, confused.
  Faces: neutral, happy, focus, wide, confused.

  Both scripts run a collision check that includes TICK's own box, because
  he once stood on a paragraph. A card that reports an overlap is a broken
  card, not a card to ship.

  No browser is involved anywhere in this. Pillow draws the pixels, a small
  Python synth writes the score, ffmpeg muxes the file.

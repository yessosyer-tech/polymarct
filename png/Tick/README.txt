POLYMARCT // TICK

TICK is the mascot. He is not a character bolted onto the brand: he is the acid
bar from the mark, stood up and given a face. In the logo that bar is the last
price, sitting in the gap between the two sides of the book, and that is what
he is. A tick is the smallest movement a price can make.

He points at real parts of the product and explains one thing at a time.

FILES

  sheet.png                       the character sheet: poses, expressions,
                                  how he reads from 190px down to 24px
  01-what-the-number-means.png    a price is the odds, not a fee
  02-why-it-moves.png             a move means somebody knew something first
  03-what-you-are-buying.png      $100 buys 149.25 shares that pay $1 each
  04-reality-decides.png          the source was named before anyone traded

  The film is dist/polymarct-05-tick-1080p.mp4, 24 seconds with sound.
  Stills from it are in png/06-film-stills as tick-*.png.

THE RULES THAT KEEP HIM THE SAME

  body        always acid #CCFF00, never recoloured, never gradient
  visor       always graphite #08090A
  eyes, arms  always warm white #F2EFE9
  head tick   up is white, down is the signal red, flat is a dash
  he floats   no legs, because a price does not walk
  he never    covers the number he is pointing at

POSES

  idle  point  cheer  think  confused  hold  press
  directions: left, right, up, down
  expressions: neutral, happy, focus, wide, confused

He can carry a number in his visor readout, which is how he shows a price or
the 51/49 face when a market is genuinely undecided.

HOW TO MAKE MORE

  He is one function, brand/mascot.js, so every still and every frame of every
  film comes from the same character rather than a redrawing of him.

    MASCOT.draw(ctx, { x, y, s, pose, dir, expr, tick, label, t })
    MASCOT.pointerLine(ctx, fromHand, toThing)

  New cards go in brand/export-mascot.html, run MC.all() in the console, then
  python tools/build_png.py. MC.collisions() must read clean for every card
  first: TICK is in the collision set, so he cannot stand on a paragraph.

VOICE

  He explains, he does not sell. Short flat lines, no exclamation marks, never
  a price prediction of his own, never a promise about returns.

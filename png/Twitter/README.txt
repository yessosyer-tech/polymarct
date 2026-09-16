POLYMARCT // TWITTER SET

Ten cards, ten layouts, 1600x900. Each one teaches a single thing about how a
prediction market works, and none of them repeat a layout. Nothing is drawn
behind type: the ground stays empty and structure does the work, so no string
ever sits on top of another. That is checked on every render, not eyeballed.

01  ANATOMY              the five parts of a market, called out on a real card
02  WHAT 67 CENTS BUYS   the payout arithmetic, start to finish
03  CALIBRATION          why a price is a claim that can be graded
04  OPINION VERSUS PRICE four takes next to four numbers
05  LIFE OF A MARKET     open, flow, event, close, verdict, on one line
06  THE VERDICT ENGINE   how a result is reached, and the dispute branch
07  WHY IT MOVED         an annotated jump with the flow that caused it
08  THE SPREAD           the order book, and where the logo comes from
09  ONE DOLLAR           why the two sides always sum to a dollar
10  THE BOARD            the live market table

HOW TO POST THEM

Lead with 01, 09 and 02. They answer "what is this" for somebody who has never
traded an outcome in their life, and they travel furthest outside crypto.

03 and 06 are the trust posts. Use them when somebody asks why they should
believe the number, or after any argument about a resolution.

04 is the quote tweet. Somebody posts a confident take with no number; you
reply with 04 and nothing else.

05 and 07 are a thread. First how a market lives, then how to read one move
inside it.

08 is the brand post. It explains the mark without saying the word logo.

10 is the daily one. Re-export it each morning and the numbers are current.

CAPTIONS

Say what the card shows, then stop. The card is the argument, and a caption
that repeats it wastes the only line anybody reads. No predictions of your own,
no promised returns, no guarantees, and never lead with the token.

REGENERATE

python tools/serve.py, open /brand/export-twitter.html, run TW.all() in the
console, then python tools/build_png.py. TW.collisions() prints a per card
overlap report and must say clean for all ten before anything ships.

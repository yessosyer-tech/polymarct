# POLYMARCT // TRAILER VOICE-OVER

30 seconds. Nine lines, 45 words. Read low, slow and certain, closer to a
financial documentary than a sportsbook ad. No hype inflection, no rising
"and MORE!" energy. The market is not excited; it is sure.

## Timecodes

| In | Line | Direction |
|---|---|---|
| 01.80 | Every day, the world argues about what happens next. | flat, observational, almost bored |
| 04.70 | Everyone has an opinion. | a shade of contempt |
| 06.20 | Nobody has a number. | land hard on **number**, then stop |
| 08.10 | Until the market gives one. | quieter, the turn of the film |
| 13.60 | One question. Two outcomes. | clipped, two beats, no warmth |
| 15.10 | Real money. Real conviction. | weight on **real** both times |
| 21.05 | Reality decides. | full stop, let the silence sit |
| 24.40 | The market pays. | matter of fact, not triumphant |
| 27.10 | Polymarct. The future has a price. | slowest line in the film |

Total speech is about 19 seconds inside a 30 second cut, so roughly a third of
the film is deliberately silent. Do not fill it.

## Getting a real voice in

The page looks for `brand/motion/audio/vo.mp3` on load. Drop a single mixed
file there, timed from 00.00, and it plays instead of the browser voice, with
no code change. Cues above are the in-points to align to.

Until that file exists, the trailer speaks the same script through the browser
speech engine. That is a scratch track for timing, not the final voice: it has
no breath, no weight and no performance. Ship the film with a recorded read or
a proper synthesis pass.

Press `V` to turn the voice off entirely, `M` to mute everything.

## Music

There is no licensed track and none is needed: the score is synthesised in the
page, locked to the same 120 BPM grid the cuts sit on. Sub, pulse, a kick on
every cut, a four second riser into the build, two hard silences (20.40 and the
beat before the logo) and one final impact under the lock. Because it is
generated from the cut list, the music cannot drift out of sync with the
picture, and there is nothing to clear for rights.

If you replace it with a licensed track, keep the two silences. They are doing
most of the work.

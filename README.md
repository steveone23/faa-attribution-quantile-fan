# FAA attribution quantile fan

An entry for the make.fun bounty **polymarket-faa-attribution-02**: forecast
Polymarket's FAA outage attribution prices minute by minute, 4 hours ahead.
For every market of a case, `main.py` writes the 5%, 25%, 50%, 75% and 95%
quantiles of the Yes price for each of the next 240 minutes. It uses the
Python standard library only, needs no network and no clock, and two runs write
identical bytes.

## How the forecast works

The program first looks at the board as a whole.

- **Independent markets (the final's FAA markets).** The median is the last
  price (persistence). The fan width at each horizon is the trailing
  realised-move fan of the same market (a fitted blend of mean absolute
  h-minute moves and EWMAs of absolute one-minute moves), scaled down a little
  and blended in quadrature with a random-walk floor that grows like the square
  root of the horizon. The floor keeps a sensible width for a market whose
  midpoint has been stuck for hours. The floor's sigma follows the market's
  own 4-hour moves, kept between a lower and an upper cap, so a market that
  has barely moved gets a lower floor than a busy one. Upside offsets are added to the price;
  downside offsets are applied multiplicatively, so the lower quantiles never
  go below zero.
- **A broad board of mutually exclusive outcomes (the NVIDIA practice).** A
  board of at least 10 markets whose last prices sum to between 0.7 and 1.3
  keeps the earlier board-aware model unchanged: mature markets get a fitted
  realised-move fan, and young markets get their own fitted fan and a shifted
  median that uses the board's total.

The board-aware branch only serves the NVIDIA practice board. The final's FAA
markets (four independent Yes/No markets) take the independent-market branch.

## Running it locally

```sh
MAKEFUN_INPUT_DIR=path/to/input MAKEFUN_OUTPUT_DIR=out python main.py
python validate.py path/to/input out
```

`main.py` reads every `*.in` file in the input directory (default `/input`)
and writes one `<id>.out` per case to the output directory (default
`/output`). `validate.py` checks each output against the bounty's shape rules
(one entry per market, 240 rows of 5 non-decreasing numbers in [0, 1], at most
1 MiB) and exits non-zero on any failure.

## License

MIT, see `LICENSE`.

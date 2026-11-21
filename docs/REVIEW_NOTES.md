# Takeover review notes

The owner-provided v7 ZIP's SHA256 matched
`68313dea2e4e301cf39b6e4d992c1e8984dc4a3e415575243f1cbdc0a13ab55f`.
It contained 12 entries, including competing v4/v7 Quant implementations. Original
bytes are retained with an inventory; the runtime no longer imports either variant.

The replacement fixes the reviewed unsafe-number/tick/negative-price paths,
SMA-seed wiring, OHLC/gap/UTC timing, direction agreement, breakout highs/lows,
ATR freezing, expiry and adverse tick rounding. Independent seeded-value and ATR
oracles test arithmetic rather than just checking that a function runs.

The regression suite retains the behavioral requirements of the earlier scanner
and Quant checks and expands them. Original test source files remain unchanged as
archival .txt files. Those historical scripts are not the active test runner, and
this report does not claim their printed PASS messages independently validate the
new implementation. See tests/test_foundation.py and tests/test_boundaries.py.

Scope deliberately stays a fixture-only foundation. New code cannot activate real
or operational paper execution. Public metadata is not automatically classified as
an approved instrument. One real public ticker request was attempted: HTTP 200
with HTML “Site Unavailable”; strict decoding correctly returned INVALID_RESPONSE.
No attempt to evade the block or claim valid live data was made.

Browser review uses the same HTML/CSS/JS with a clearly labelled static fixture
adapter because the managed preview runtime could not launch the Python interpreter.
The API was exercised separately through actual loopback HTTP integration tests.
Static browser interaction is not evidence of end-to-end native bot connectivity.

Please review the policy/risk arithmetic, source timing, schema 3.0, private-round
boundary and demo lifecycle independently. Grok's proposals are welcome. No claim
of production safety, profitability or guaranteed intelligence follows from passing
these tests. All native and continuous-operation gates remain explicit.

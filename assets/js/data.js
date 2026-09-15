/* POLYMARCT / market universe
   Demo dataset. Every market carries explicit resolution criteria and a source,
   because a market without a defined verdict is not a market. */

const CATEGORIES = ["CRYPTO", "ARC", "POLITICS", "SPORTS", "TECHNOLOGY", "BUSINESS", "CULTURE"];

const MARKETS = [
  // ---------------- CRYPTO ----------------
  { id:"btc-125k", cat:"CRYPTO", q:"Will BTC reach $125,000 before October 31?", yes:0.67, d24:0.084, vol:4820000, liq:1240000, traders:18421, ends:"2026-10-31T23:59:00Z",
    src:"Coinbase BTC-USD spot, hourly close", crit:"YES if the hourly close on Coinbase BTC-USD prints at or above $125,000.00 at any point before the resolution time.", tags:["BTC","crypto-liquidity","macro"] },
  { id:"eth-5k", cat:"CRYPTO", q:"Will ETH trade above $5,000 this quarter?", yes:0.41, d24:-0.031, vol:2140000, liq:680000, traders:9120, ends:"2026-12-31T23:59:00Z",
    src:"Coinbase ETH-USD spot, hourly close", crit:"YES if the hourly close on Coinbase ETH-USD prints at or above $5,000.00 before the resolution time.", tags:["ETH","BTC","crypto-liquidity"] },
  { id:"sol-flip", cat:"CRYPTO", q:"Will SOL market cap exceed 25% of ETH market cap in 2026?", yes:0.23, d24:0.012, vol:880000, liq:310000, traders:4310, ends:"2026-12-31T23:59:00Z",
    src:"CoinGecko daily market cap snapshot, 00:00 UTC", crit:"YES if SOL circulating market cap divided by ETH circulating market cap is at or above 0.25 on any daily snapshot.", tags:["SOL","ETH"] },
  { id:"etf-inflow", cat:"CRYPTO", q:"Will spot BTC ETFs record a $2B net inflow week before December?", yes:0.58, d24:0.121, vol:3310000, liq:940000, traders:12880, ends:"2026-12-01T00:00:00Z",
    src:"Farside Investors weekly aggregate net flow", crit:"YES if any Monday-to-Friday aggregate net flow across US spot BTC ETFs is at or above $2.00B.", tags:["ETF","BTC","crypto-liquidity","rates"] },
  { id:"stable-300", cat:"CRYPTO", q:"Will total stablecoin supply cross $300B this year?", yes:0.74, d24:0.022, vol:1620000, liq:520000, traders:7740, ends:"2026-12-31T23:59:00Z",
    src:"DefiLlama stablecoins total circulating", crit:"YES if DefiLlama total stablecoin circulating supply reports at or above $300.0B on any daily snapshot.", tags:["stablecoins","crypto-liquidity","ARC"] },
  { id:"usdc-share", cat:"CRYPTO", q:"Will USDC exceed 30% of stablecoin supply before year end?", yes:0.36, d24:0.048, vol:740000, liq:260000, traders:3980, ends:"2026-12-31T23:59:00Z",
    src:"DefiLlama stablecoin dominance", crit:"YES if USDC circulating supply divided by total stablecoin circulating supply is at or above 0.30 on any daily snapshot.", tags:["stablecoins","USDC","ARC"] },
  { id:"defi-hack", cat:"CRYPTO", q:"Will a single DeFi exploit exceed $100M this quarter?", yes:0.31, d24:-0.019, vol:620000, liq:190000, traders:2910, ends:"2026-12-31T23:59:00Z",
    src:"Rekt leaderboard, confirmed loss figure", crit:"YES if a single confirmed exploit with a loss at or above $100M is listed with an incident date inside the window.", tags:["security","DeFi"] },
  { id:"btc-dom", cat:"CRYPTO", q:"Will BTC dominance fall below 50% before November?", yes:0.44, d24:0.067, vol:1180000, liq:410000, traders:6220, ends:"2026-11-01T00:00:00Z",
    src:"TradingView BTC.D daily close", crit:"YES if BTC.D daily close prints below 50.00% at least once before the resolution time.", tags:["BTC","crypto-liquidity"] },
  { id:"alt-season", cat:"CRYPTO", q:"Will 75% of the top 50 alts outperform BTC over any 30-day window this quarter?", yes:0.28, d24:0.034, vol:520000, liq:170000, traders:2440, ends:"2026-12-31T23:59:00Z",
    src:"CoinGecko top 50 by market cap, 30-day returns", crit:"YES if on any daily snapshot at least 38 of the top 50 non-BTC assets show a higher trailing 30-day return than BTC.", tags:["BTC","crypto-liquidity"] },
  { id:"l2-tvl", cat:"CRYPTO", q:"Will combined L2 TVL set a new all-time high before December?", yes:0.62, d24:0.015, vol:940000, liq:330000, traders:5110, ends:"2026-12-01T00:00:00Z",
    src:"L2Beat total value secured", crit:"YES if L2Beat total value secured closes above its prior all-time high on any daily snapshot.", tags:["L2","TVL"] },
  { id:"cb-listing", cat:"CRYPTO", q:"Will Coinbase list a new top-100 asset in October?", yes:0.81, d24:0.009, vol:410000, liq:140000, traders:2010, ends:"2026-10-31T23:59:00Z",
    src:"Coinbase official listing blog", crit:"YES if Coinbase publishes a trading launch for an asset inside the CoinGecko top 100 at announcement time.", tags:["exchange"] },
  { id:"fed-crypto", cat:"CRYPTO", q:"Will the Fed cut rates at the next meeting?", yes:0.71, d24:0.112, vol:6240000, liq:1810000, traders:24100, ends:"2026-11-05T21:00:00Z",
    src:"FOMC official statement", crit:"YES if the published statement sets a target range below the prior range.", tags:["Fed","rates","macro","crypto-liquidity"] },

  // ---------------- ARC ----------------
  { id:"arc-1m-tx", cat:"ARC", q:"Will Arc exceed 1M daily transactions before November?", yes:0.42, d24:0.061, vol:1340000, liq:520000, traders:8840, ends:"2026-11-01T00:00:00Z",
    src:"Arc public block explorer, daily transaction count", crit:"YES if the explorer reports a UTC-day transaction count at or above 1,000,000.", tags:["ARC","network"] },
  { id:"arc-tvl-100", cat:"ARC", q:"Which Arc protocol reaches $100M TVL first?", yes:0.37, d24:0.028, vol:2210000, liq:760000, traders:11240, ends:"2026-12-31T23:59:00Z",
    src:"DefiLlama Arc chain TVL by protocol", crit:"YES resolves on the named protocol reaching $100M TVL on a daily snapshot before any other Arc protocol.", tags:["ARC","TVL","DeFi"] },
  { id:"arc-stable-1b", cat:"ARC", q:"Will stablecoin supply on Arc pass $1B this year?", yes:0.56, d24:0.043, vol:1720000, liq:610000, traders:9310, ends:"2026-12-31T23:59:00Z",
    src:"DefiLlama Arc stablecoin supply", crit:"YES if reported stablecoin circulating supply on Arc is at or above $1.00B on any daily snapshot.", tags:["ARC","stablecoins","USDC"] },
  { id:"arc-100k-wallets", cat:"ARC", q:"Will Arc pass 100,000 weekly active addresses?", yes:0.49, d24:0.017, vol:680000, liq:240000, traders:4420, ends:"2026-12-31T23:59:00Z",
    src:"Arc explorer, unique sending addresses per 7-day window", crit:"YES if any rolling 7-day window reports at or above 100,000 unique sending addresses.", tags:["ARC","network"] },
  { id:"arc-dex-vol", cat:"ARC", q:"Will a single Arc DEX clear $500M weekly volume?", yes:0.33, d24:0.052, vol:910000, liq:320000, traders:5180, ends:"2026-12-31T23:59:00Z",
    src:"DefiLlama DEX volume, Arc chain filter", crit:"YES if any single Arc DEX reports at or above $500M volume across a Monday-to-Sunday window.", tags:["ARC","DEX","volume"] },
  { id:"arc-nonarc", cat:"ARC", q:"Will a non-ARC asset become the largest asset by value held on Arc?", yes:0.64, d24:-0.024, vol:540000, liq:190000, traders:3140, ends:"2026-12-31T23:59:00Z",
    src:"Arc explorer token holdings ranking", crit:"YES if any non-ARC token holds the top position by aggregate USD value on a daily snapshot.", tags:["ARC","stablecoins"] },
  { id:"arc-perps", cat:"ARC", q:"Will a perps venue launch on Arc before October 1?", yes:0.71, d24:0.038, vol:760000, liq:280000, traders:4010, ends:"2026-10-01T00:00:00Z",
    src:"Protocol mainnet announcement plus verified on-chain activity", crit:"YES if a perpetual futures venue is live on Arc mainnet with non-zero user volume before the resolution time.", tags:["ARC","DeFi","perps"] },
  { id:"arc-fee-stable", cat:"ARC", q:"Will median Arc transaction fees stay under $0.01 all quarter?", yes:0.78, d24:0.006, vol:430000, liq:160000, traders:2380, ends:"2026-12-31T23:59:00Z",
    src:"Arc explorer, daily median fee in USDC", crit:"YES if no UTC day inside the window reports a median fee above $0.0100.", tags:["ARC","network","fees"] },
  { id:"arc-polymarct", cat:"ARC", q:"Will Polymarct clear $10M cumulative volume in its first 90 days?", yes:0.52, d24:0.094, vol:1130000, liq:390000, traders:6720, ends:"2026-12-14T00:00:00Z",
    src:"Polymarct settlement contract, cumulative matched notional", crit:"YES if cumulative matched notional across all markets is at or above $10.0M within 90 days of mainnet launch.", tags:["ARC","PMARC","volume"] },
  { id:"arc-institution", cat:"ARC", q:"Will a regulated institution announce settlement on Arc this year?", yes:0.38, d24:0.021, vol:620000, liq:210000, traders:3320, ends:"2026-12-31T23:59:00Z",
    src:"Primary company announcement or regulatory filing", crit:"YES if a licensed bank, broker-dealer or payments institution publicly confirms production settlement on Arc.", tags:["ARC","institutions","stablecoins"] },
  { id:"arc-bridge", cat:"ARC", q:"Will Arc bridged value exceed $2B before year end?", yes:0.45, d24:-0.012, vol:490000, liq:170000, traders:2610, ends:"2026-12-31T23:59:00Z",
    src:"DefiLlama bridged TVL, Arc", crit:"YES if reported bridged value on Arc is at or above $2.00B on any daily snapshot.", tags:["ARC","TVL","bridge"] },

  // ---------------- TECHNOLOGY ----------------
  { id:"openai-model", cat:"TECHNOLOGY", q:"Will OpenAI ship a new frontier model before December?", yes:0.69, d24:0.041, vol:2840000, liq:820000, traders:14210, ends:"2026-12-01T00:00:00Z",
    src:"OpenAI official product blog", crit:"YES if OpenAI publishes general availability of a model it labels as a new frontier or flagship release.", tags:["AI","OpenAI"] },
  { id:"apple-ai", cat:"TECHNOLOGY", q:"Will Apple announce an AI hardware product this year?", yes:0.34, d24:-0.028, vol:1210000, liq:410000, traders:6840, ends:"2026-12-31T23:59:00Z",
    src:"Apple Newsroom announcement", crit:"YES if Apple announces a new hardware product whose primary marketed function is on-device AI.", tags:["AI","Apple"] },
  { id:"ai-capex", cat:"TECHNOLOGY", q:"Will combined hyperscaler AI capex guidance exceed $400B for next year?", yes:0.61, d24:0.033, vol:1640000, liq:560000, traders:8120, ends:"2027-02-28T23:59:00Z",
    src:"Company earnings calls and filings", crit:"YES if the sum of published capex guidance from the four largest US hyperscalers is at or above $400B.", tags:["AI","earnings","business"] },
  { id:"starship", cat:"TECHNOLOGY", q:"Will Starship complete an orbital refuelling demo before June?", yes:0.29, d24:0.018, vol:880000, liq:290000, traders:4610, ends:"2027-06-01T00:00:00Z",
    src:"SpaceX and NASA official confirmation", crit:"YES if both parties confirm a propellant transfer between two vehicles in orbit.", tags:["space","SpaceX"] },
  { id:"agent-standard", cat:"TECHNOLOGY", q:"Will a major agent interop standard reach three frontier labs?", yes:0.47, d24:0.072, vol:610000, liq:220000, traders:3240, ends:"2026-12-31T23:59:00Z",
    src:"Public documentation from each lab", crit:"YES if three of the named frontier labs document production support for the same agent interop protocol.", tags:["AI","standards"] },
  { id:"quantum", cat:"TECHNOLOGY", q:"Will a verified quantum advantage claim survive peer review this year?", yes:0.19, d24:-0.008, vol:340000, liq:120000, traders:1840, ends:"2026-12-31T23:59:00Z",
    src:"Peer-reviewed publication in a listed journal", crit:"YES if a quantum advantage result is published and not retracted within the window.", tags:["science","quantum"] },
  { id:"chip-export", cat:"TECHNOLOGY", q:"Will new AI chip export restrictions be announced before year end?", yes:0.55, d24:0.026, vol:1420000, liq:470000, traders:7310, ends:"2026-12-31T23:59:00Z",
    src:"Federal Register publication", crit:"YES if a new rule restricting advanced AI accelerator exports is published in the Federal Register.", tags:["AI","policy","chips"] },

  // ---------------- POLITICS ----------------
  { id:"fed-chair", cat:"POLITICS", q:"Will the next Fed chair nominee be announced before January?", yes:0.48, d24:0.055, vol:3120000, liq:980000, traders:16420, ends:"2027-01-01T00:00:00Z",
    src:"White House official announcement", crit:"YES if a formal nomination is announced before the resolution time.", tags:["Fed","rates","policy","macro"] },
  { id:"gov-shutdown", cat:"POLITICS", q:"Will there be a US government shutdown this quarter?", yes:0.26, d24:-0.043, vol:2410000, liq:740000, traders:13120, ends:"2026-12-31T23:59:00Z",
    src:"OMB lapse in appropriations notice", crit:"YES if a funding lapse begins inside the window.", tags:["policy","macro"] },
  { id:"eu-crypto", cat:"POLITICS", q:"Will the EU open a formal review of MiCA before July?", yes:0.42, d24:0.014, vol:640000, liq:210000, traders:3410, ends:"2027-07-01T00:00:00Z",
    src:"Official Journal of the European Union", crit:"YES if a formal review or amendment procedure is published.", tags:["policy","EU","crypto"] },
  { id:"stable-bill", cat:"POLITICS", q:"Will a US stablecoin framework pass both chambers this session?", yes:0.37, d24:0.081, vol:2870000, liq:910000, traders:15240, ends:"2027-01-03T00:00:00Z",
    src:"Congress.gov bill status", crit:"YES if the same bill text passes the House and the Senate inside the session.", tags:["policy","stablecoins","USDC"] },
  { id:"uk-election", cat:"POLITICS", q:"Will a UK general election be called before May?", yes:0.22, d24:-0.011, vol:980000, liq:320000, traders:5210, ends:"2027-05-01T00:00:00Z",
    src:"UK Parliament dissolution notice", crit:"YES if dissolution is formally announced before the resolution time.", tags:["policy","UK"] },
  { id:"cbdc", cat:"POLITICS", q:"Will a G7 central bank launch a retail CBDC pilot this year?", yes:0.31, d24:0.007, vol:520000, liq:180000, traders:2840, ends:"2026-12-31T23:59:00Z",
    src:"Central bank official publication", crit:"YES if a G7 central bank opens a retail pilot to public participants.", tags:["policy","CBDC","stablecoins"] },
  { id:"sanctions", cat:"POLITICS", q:"Will new sanctions target a major crypto venue before December?", yes:0.29, d24:0.019, vol:440000, liq:150000, traders:2210, ends:"2026-12-01T00:00:00Z",
    src:"OFAC SDN list updates", crit:"YES if a venue inside the top 20 by reported volume is added to the SDN list.", tags:["policy","exchange"] },

  // ---------------- SPORTS ----------------
  { id:"champions", cat:"SPORTS", q:"Will an English club win the Champions League?", yes:0.44, d24:0.026, vol:3840000, liq:1120000, traders:21420, ends:"2027-05-29T21:00:00Z",
    src:"UEFA official result", crit:"YES if the club lifting the trophy is registered in the English top flight.", tags:["football","UEFA"] },
  { id:"superbowl", cat:"SPORTS", q:"Will the Super Bowl total points exceed 48.5?", yes:0.51, d24:-0.014, vol:4210000, liq:1340000, traders:26810, ends:"2027-02-08T04:00:00Z",
    src:"NFL official final score", crit:"YES if combined final points are 49 or higher.", tags:["NFL"] },
  { id:"f1-title", cat:"SPORTS", q:"Will the F1 title be decided before the final race?", yes:0.38, d24:0.031, vol:1240000, liq:410000, traders:7120, ends:"2026-11-22T18:00:00Z",
    src:"FIA official standings", crit:"YES if a driver is mathematically champion before the final round begins.", tags:["F1"] },
  { id:"nba-record", cat:"SPORTS", q:"Will any NBA team win 65 or more games this season?", yes:0.33, d24:0.009, vol:1610000, liq:520000, traders:9240, ends:"2027-04-15T23:59:00Z",
    src:"NBA official standings at end of regular season", crit:"YES if at least one team records 65 or more regular season wins.", tags:["NBA"] },
  { id:"marathon", cat:"SPORTS", q:"Will the marathon world record fall this year?", yes:0.24, d24:0.017, vol:410000, liq:130000, traders:2110, ends:"2026-12-31T23:59:00Z",
    src:"World Athletics ratified record", crit:"YES if World Athletics ratifies a faster mark inside the window.", tags:["athletics"] },

  // ---------------- BUSINESS ----------------
  { id:"nvda-earnings", cat:"BUSINESS", q:"Will NVDA beat consensus revenue next quarter?", yes:0.72, d24:0.038, vol:5120000, liq:1620000, traders:22140, ends:"2026-11-20T21:00:00Z",
    src:"Company earnings release versus Refinitiv consensus", crit:"YES if reported revenue exceeds the consensus estimate published on the day before the release.", tags:["earnings","AI","business"] },
  { id:"ipo-window", cat:"BUSINESS", q:"Will three or more $5B+ IPOs price before year end?", yes:0.41, d24:0.024, vol:1320000, liq:440000, traders:6810, ends:"2026-12-31T23:59:00Z",
    src:"SEC filings and pricing announcements", crit:"YES if at least three IPOs price at a fully diluted valuation at or above $5B.", tags:["IPO","business"] },
  { id:"big-acq", cat:"BUSINESS", q:"Will a $10B+ acquisition be announced in fintech this quarter?", yes:0.36, d24:0.058, vol:940000, liq:310000, traders:4720, ends:"2026-12-31T23:59:00Z",
    src:"Definitive agreement press release", crit:"YES if a definitive agreement with announced consideration at or above $10B is published.", tags:["MandA","fintech","business"] },
  { id:"oil-90", cat:"BUSINESS", q:"Will Brent crude close above $90 before December?", yes:0.27, d24:-0.036, vol:1840000, liq:610000, traders:8410, ends:"2026-12-01T00:00:00Z",
    src:"ICE Brent front month settlement", crit:"YES if any front month settlement prints at or above $90.00.", tags:["oil","macro","rates"] },

  // ---------------- CULTURE ----------------
  { id:"box-office", cat:"CULTURE", q:"Will any film cross $1B global box office this quarter?", yes:0.58, d24:0.022, vol:820000, liq:270000, traders:5140, ends:"2026-12-31T23:59:00Z",
    src:"Box Office Mojo worldwide gross", crit:"YES if a single title reports worldwide gross at or above $1.000B inside the window.", tags:["film"] },
  { id:"album-1", cat:"CULTURE", q:"Will a debut artist take the Billboard 200 number one before year end?", yes:0.31, d24:0.014, vol:410000, liq:140000, traders:2410, ends:"2026-12-31T23:59:00Z",
    src:"Billboard 200 published chart", crit:"YES if an artist with no prior charting album reaches number one.", tags:["music"] },
  { id:"ai-film", cat:"CULTURE", q:"Will a majority-AI-generated film get a wide theatrical release?", yes:0.17, d24:0.028, vol:340000, liq:110000, traders:1810, ends:"2027-06-30T23:59:00Z",
    src:"Distributor release announcement plus production disclosure", crit:"YES if a film disclosed as majority AI generated opens in 600 or more screens.", tags:["AI","film"] },
  { id:"creator-exit", cat:"CULTURE", q:"Will a top-10 creator sign a nine-figure platform deal this year?", yes:0.44, d24:0.019, vol:520000, liq:170000, traders:2940, ends:"2026-12-31T23:59:00Z",
    src:"Platform or creator public confirmation with reported figure", crit:"YES if a deal with reported value at or above $100M is publicly confirmed.", tags:["creators","business"] }
];

/* Arc network telemetry (demo values) */
const ARC_NETWORK = [
  { k:"TRANSACTIONS / 24H", v:"842,104", d:"+12.4% vs 7d avg", up:true },
  { k:"TOTAL VALUE LOCKED", v:"$1.82B", d:"+4.1% / 24h", up:true },
  { k:"STABLECOIN SUPPLY", v:"$742.6M", d:"+2.8% / 24h", up:true },
  { k:"ACTIVE ADDRESSES / 7D", v:"88,412", d:"+9.6% / 7d", up:true },
  { k:"DEX VOLUME / 24H", v:"$412.8M", d:"-3.2% / 24h", up:false },
  { k:"MEDIAN FEE", v:"$0.0021", d:"USDC denominated", up:true }
];

const ARC_PROTOCOLS = [
  { n:"Meridian", t:"DEX", tvl:284000000, vol:142000000, users:24810, g:0.184 },
  { n:"Vault Arc", t:"LENDING", tvl:212000000, vol:38000000, users:12140, g:0.092 },
  { n:"Polymarct", t:"PREDICTION", tvl:118000000, vol:94000000, users:18421, g:0.412 },
  { n:"Settle", t:"PAYMENTS", tvl:96000000, vol:221000000, users:41220, g:0.061 },
  { n:"Loop", t:"PERPS", tvl:84000000, vol:186000000, users:9840, g:0.238 },
  { n:"Anchor Arc", t:"YIELD", tvl:61000000, vol:12000000, users:6410, g:-0.042 },
  { n:"Relay", t:"BRIDGE", tvl:48000000, vol:74000000, users:15210, g:0.118 },
  { n:"Ledgerworks", t:"RWA", tvl:39000000, vol:8000000, users:1840, g:0.294 }
];

/* Conviction index (anti-gaming: rank is risk adjusted, not by size) */
const TRADERS = [
  { w:"0x82...91A", conv:94.2, roi:0.412, acc:0.68, n:284, vol:1840000, streak:"11 resolved" },
  { w:"0x71...42B", conv:91.8, roi:0.336, acc:0.71, n:164, vol:920000, streak:"7 resolved" },
  { w:"0x19...A21", conv:88.4, roi:0.291, acc:0.64, n:412, vol:3120000, streak:"4 resolved" },
  { w:"0xC4...07F", conv:85.1, roi:0.248, acc:0.62, n:198, vol:640000, streak:"9 resolved" },
  { w:"0x3A...DD2", conv:82.6, roi:0.221, acc:0.66, n:121, vol:410000, streak:"3 resolved" },
  { w:"0x9F...5B8", conv:79.9, roi:0.194, acc:0.59, n:346, vol:2240000, streak:"2 resolved" },
  { w:"0x2D...16C", conv:77.4, roi:0.171, acc:0.61, n:142, vol:380000, streak:"6 resolved" },
  { w:"0xE1...88A", conv:74.8, roi:0.148, acc:0.57, n:264, vol:1120000, streak:"1 resolved" },
  { w:"0x66...3C4", conv:72.1, roi:0.132, acc:0.58, n:98, vol:240000, streak:"5 resolved" },
  { w:"0xB0...74E", conv:69.5, roi:0.118, acc:0.55, n:186, vol:690000, streak:"2 resolved" }
];

/* Aggregate themes for WHAT THE WORLD THINKS */
const THEMES = [
  { n:"CRYPTO", tags:["BTC","ETH","crypto-liquidity","stablecoins"], read:"Bullish" },
  { n:"AI", tags:["AI"], read:"Bullish" },
  { n:"US ECONOMY", tags:["macro","rates","Fed","policy"], read:"Neutral" },
  { n:"TECHNOLOGY", tags:["AI","chips","space","standards"], read:"Bullish" },
  { n:"ARC", tags:["ARC"], read:"Bullish" },
  { n:"RISK", tags:["security","policy","oil"], read:"Bearish" }
];

const FUTURE_INDEX_MEMBERS = ["btc-125k","eth-5k","fed-crypto","openai-model","ai-capex","arc-1m-tx","nvda-earnings","stable-300","etf-inflow","chip-export"];

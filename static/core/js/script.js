document.addEventListener("DOMContentLoaded", () => {

  const hamburger = document.getElementById("hamburger");
  const nav = document.getElementById("navMenu");
  const darkToggle = document.getElementById("darkToggle");
  const userBtn = document.getElementById("userBtn");

  // MENU (safe check added)
  if (hamburger && nav) {
    hamburger.addEventListener("click", () => {
      nav.classList.toggle("active");
      hamburger.classList.toggle("open");
    });
  }

  // CLOSE MENU
  document.querySelectorAll(".nav a").forEach(link => {
    link.addEventListener("click", () => {
      nav.classList.remove("active");
      hamburger.classList.remove("open");
    });
  });

  // DARK MODE
  const saved = localStorage.getItem("theme");
  if (saved === "dark") document.body.classList.add("dark");

  if (darkToggle) {
    darkToggle.addEventListener("click", () => {
      document.body.classList.toggle("dark");
      localStorage.setItem(
        "theme",
        document.body.classList.contains("dark") ? "dark" : "light"
      );
    });
  }

  // LOGIN
  if (userBtn) {
    userBtn.addEventListener("click", () => {
      window.location.href = "login.html";
    });
  }

  /* =========================
     SNOW (STABLE VERSION)
  ========================= */

  if (window.tsParticles) {
    tsParticles.load("tsparticles", {
      fullScreen: {
        enable: true,
        zIndex: 0   // 🔥 FIX: prevents covering navbar/Google translate
      },

      particles: {
        number: {
          value: 150,
          density: {
            enable: true,
            area: 1200
          }
        },

        color: {
          value: ["#ffffff", "#e5e7eb"]
        },

        shape: {
          type: "circle"
        },

        opacity: {
          value: 0.35
        },

        size: {
          value: { min: 0.3, max: 1.2 }
        },

        move: {
          enable: true,
          speed: 0.08,
          direction: "bottom",
          random: false,
          straight: false,

          gravity: {
            enable: true,
            acceleration: 0.02
          },

          drift: 0,

          outModes: {
            default: "out"
          }
        }
      },

      interactivity: {
        events: {
          onHover: {
            enable: false
          }
        }
      },

      detectRetina: true
    });
  }
/* =========================
   TRANSACTION TABS
========================= */

const withdrawTab = document.getElementById("withdrawTab");
const investTab = document.getElementById("investTab");

const withdrawals = document.getElementById("withdrawals");
const investments = document.getElementById("investments");

if (withdrawTab && investTab && withdrawals && investments) {

  // DEFAULT STATE
  withdrawals.style.display = "block";
  investments.style.display = "none";

  withdrawTab.classList.add("active");

  withdrawTab.addEventListener("click", () => {
    withdrawals.style.display = "block";
    investments.style.display = "none";

    withdrawTab.classList.add("active");
    investTab.classList.remove("active");
  });

  investTab.addEventListener("click", () => {
    withdrawals.style.display = "none";
    investments.style.display = "block";

    investTab.classList.add("active");
    withdrawTab.classList.remove("active");
  });
}


/* =========================
   REALISTIC DATA SET
========================= */

const names = [
  "James", "Michael", "Sarah", "Daniel", "Olivia",
  "David", "Sophia", "Ethan", "Lucas", "Emma",
  "Noah", "Ava", "Mason", "Isabella", "Liam"
];

const coins = ["Bitcoin", "Ethereum", "USDT", "Solana"];

const amounts = [500, 10000, 1000, 3000, 20000, 500, 1000, 2500, 4200];


/* =========================
   HELPERS
========================= */

function randomItem(arr) {
  return arr[Math.floor(Math.random() * arr.length)];
}

/* REALISTIC TXID */
function generateTxid() {
  const chars = "abcdef0123456789";
  let txid = "0x";
  for (let i = 0; i < 64; i++) {
    txid += chars[Math.floor(Math.random() * chars.length)];
  }
  return txid;
}

/* SHORT TXID (MOBILE FRIENDLY) */
function shortTxid(txid) {
  return txid.slice(0, 6) + "..." + txid.slice(-6);
}

/* CLEAN TIME */
function getTime() {
  const now = new Date();
  return now.toISOString().replace("T", " ").substring(0, 16);
}


/* =========================
   TRANSACTION GENERATOR
========================= */

function generateTransaction(type) {
  return {
    name: randomItem(names),
    amount: randomItem(amounts),
    coin: randomItem(coins),
    time: getTime(),
    txid: generateTxid(),
    type
  };
}


/* =========================
   ROW BUILDER
========================= */

function createRow(data) {
  return `
    <div class="transaction-row">

      <div class="tx-left">
        <div class="tx-name">${data.name}</div>
        <div class="tx-time">${data.time}</div>
        <div class="txid">${shortTxid(data.txid)}</div>
      </div>

      <div class="tx-center"></div>

      <div class="tx-right">
        <div class="tx-coin">${data.coin}</div>
        <div class="tx-amount">$${data.amount}</div>
      </div>

    </div>
  `;
}


/* =========================
   LIVE FEED ENGINE
========================= */

function addTransaction() {

  const isWithdraw = Math.random() > 0.5;
  const data = generateTransaction(isWithdraw ? "withdraw" : "invest");

  const container = isWithdraw ? withdrawals : investments;
  if (!container) return;

  container.insertAdjacentHTML("afterbegin", createRow(data));
}


/* =========================
   AUTO LIVE UPDATE (BINANCE STYLE LIMIT)
========================= */

const MAX_ROWS = 3;

setInterval(() => {

  const activeContainer =
    document.querySelector("#withdrawals:not([style*='none'])") ||
    document.querySelector("#investments:not([style*='none'])");

  if (!activeContainer) return;

  const rows = activeContainer.querySelectorAll(".transaction-row");

  // KEEP ONLY 3 ROWS
  if (rows.length >= MAX_ROWS) {
    const last = rows[rows.length - 1];

    last.style.opacity = "0";
    last.style.transform = "translateY(10px)";

    setTimeout(() => {
      last.remove();
    }, 200);
  }

  addTransaction();

}, 5000);

  /* =========================
   LIVE CRYPTO NEWS TERMINAL (BINANCE STYLE)
========================= */

const newsPool = [
  { title: "Bitcoin breaks key resistance level", meta: "BTC • Live", tag: "Market" },
  { title: "Ethereum scaling upgrade increases throughput", meta: "ETH • Live", tag: "Tech" },
  { title: "Global markets react to Fed rate signals", meta: "Macro • Live", tag: "Market" },
  { title: "AI tokens surge after institutional inflow", meta: "AI • Trending", tag: "Crypto" },
  { title: "Solana hits new transaction speed record", meta: "SOL • Live", tag: "Blockchain" },
  { title: "USDT liquidity increases across exchanges", meta: "Stablecoin • Live", tag: "Crypto" },
  { title: "Tech stocks rally on earnings surprise", meta: "Stocks • Hot", tag: "Market" },
  { title: "Crypto volatility spikes across major pairs", meta: "Market • Alert", tag: "Crypto" }
];

const tickerPool = [
  "Bitcoin surges past resistance zone",
  "Ethereum network upgrade goes live",
  "Global liquidity shifts into crypto",
  "Institutional buying pressure increases",
  "Market volatility increases sharply",
  "AI sector leads tech rally",
  "Stablecoins see record inflows"
];

/* =========================
   RANDOM HELPERS
========================= */

function random(arr) {
  return arr[Math.floor(Math.random() * arr.length)];
}

/* =========================
   LIVE TICKER (BINANCE STYLE STREAM)
========================= */

function updateTicker() {
  const track = document.getElementById("tickerTrack");
  if (!track) return;

  const span = document.createElement("span");
  span.innerHTML = "⚡ " + random(tickerPool);

  // smooth entry animation
  span.style.opacity = "0";
  span.style.transform = "translateY(10px)";
  span.style.transition = "0.4s ease";

  track.appendChild(span);

  setTimeout(() => {
    span.style.opacity = "1";
    span.style.transform = "translateY(0)";
  }, 50);

  // limit length (like real terminal feed)
  if (track.children.length > 12) {
    track.removeChild(track.firstElementChild);
  }
}

/* =========================
   REAL BINANCE LIVE DASHBOARD
========================= */

/* -------------------------
   CONFIG (BINANCE PUBLIC API)
------------------------- */

const BINANCE_API = "https://api.binance.com/api/v3/ticker/24hr?symbols=";

const symbols = [
  "BTCUSDT",
  "ETHUSDT",
  "SOLUSDT",
  "BNBUSDT",
  "XRPUSDT"
];

/* -------------------------
   STATE CACHE
------------------------- */

let previousPrices = {};


/* -------------------------
   FETCH BINANCE DATA
------------------------- */

async function fetchMarketData() {
  try {
    const url = BINANCE_API + encodeURIComponent(JSON.stringify(symbols));
    const res = await fetch(url);
    const data = await res.json();

    return data;
  } catch (err) {
    console.error("Binance API error:", err);
    return [];
  }
}


/* -------------------------
   FORMAT HELPERS
------------------------- */

function formatPrice(price) {
  return parseFloat(price).toFixed(2);
}

function formatPercent(pct) {
  return parseFloat(pct).toFixed(2);
}


/* -------------------------
   GENERATE LIVE NEWS FROM PRICE MOVEMENT
------------------------- */

function generateNewsFromMarket(marketData) {
  const news = [];

  marketData.forEach(asset => {
    const symbol = asset.symbol;
    const price = parseFloat(asset.lastPrice);
    const change = parseFloat(asset.priceChangePercent);

    let direction = change >= 0 ? "surges" : "drops";

    let title = "";

    if (symbol === "BTCUSDT") {
      title = `Bitcoin ${direction} ${Math.abs(change).toFixed(2)}% to $${formatPrice(price)}`;
    }

    if (symbol === "ETHUSDT") {
      title = `Ethereum ${direction} after market move (${change.toFixed(2)}%)`;
    }

    if (symbol === "SOLUSDT") {
      title = `Solana shows strong volatility (${change.toFixed(2)}%)`;
    }

    if (symbol === "BNBUSDT") {
      title = `BNB reacts to exchange activity (${change.toFixed(2)}%)`;
    }

    if (symbol === "XRPUSDT") {
      title = `XRP market momentum shifts (${change.toFixed(2)}%)`;
    }

    news.push({
      title,
      meta: `${symbol} • Live Binance`,
      tag: change >= 0 ? "GAIN" : "LOSS"
    });
  });

  return news;
}


/* -------------------------
   TICKER (BINANCE STYLE)
------------------------- */

function updateTickerFromMarket(news) {
  const track = document.getElementById("tickerTrack");
  if (!track) return;

  const item = document.createElement("span");
  item.className = "ticker-item";

  const randomNews = news[Math.floor(Math.random() * news.length)];
  item.textContent = "⚡ " + randomNews.title;

  item.style.opacity = "0";
  item.style.transform = "translateY(6px)";
  item.style.transition = "all 0.3s ease";

  track.appendChild(item);

  requestAnimationFrame(() => {
    item.style.opacity = "1";
    item.style.transform = "translateY(0)";
  });

  if (track.children.length > 12) {
    track.removeChild(track.firstElementChild);
  }
}


/* -------------------------
   UPDATE NEWS CARDS (REAL DATA)
------------------------- */

function updateNewsCards(marketNews) {
  const cards = document.querySelectorAll(".news-card");
  if (!cards.length) return;

  cards.forEach((card, i) => {
    const data = marketNews[i % marketNews.length];

    const title = card.querySelector(".news-title");
    const meta = card.querySelector(".news-meta");
    const badge = card.querySelector(".news-badge");

    if (!title || !meta || !badge) return;

    card.style.opacity = "0.5";
    card.style.transform = "scale(0.98)";

    setTimeout(() => {
      title.textContent = data.title;
      meta.textContent = data.meta;
      badge.textContent = data.tag;

      card.style.opacity = "1";
      card.style.transform = "scale(1)";
    }, 200 + i * 100);
  });
}


/* -------------------------
   MAIN ENGINE LOOP
------------------------- */

async function runDashboard() {
  const marketData = await fetchMarketData();

  if (!marketData.length) return;

  const news = generateNewsFromMarket(marketData);

  updateTickerFromMarket(news);
  updateNewsCards(news);
}


/* -------------------------
   LIVE LOOP (BINANCE STYLE)
------------------------- */

function startLive() {
  runDashboard();

  // fast ticker feel
  setInterval(runDashboard, 4000);
}


/* -------------------------
   INIT
------------------------- */

document.addEventListener("DOMContentLoaded", startLive);



async function loadStats() {
  const res = await fetch("http://localhost:3000/stats");
  const data = await res.json();

  document.getElementById("totalSubs").innerText = data.totalUsers;
  document.getElementById("totalRefs").innerText = data.totalRefs;
  document.getElementById("liveSignups").innerText = data.liveSignups;
  document.getElementById("convRate").innerText = data.conversion + "%";
}

async function loadLeaderboard() {
  const res = await fetch("http://localhost:3000/leaderboard");
  const data = await res.json();

  const board = document.getElementById("leaderboard");
  board.innerHTML = "";

  data.forEach(item => {
    const div = document.createElement("div");
    div.className = "leader-item";
    div.innerHTML = `
      <span>${item.ref}</span>
      <b>${item.count}</b>
    `;
    board.appendChild(div);
  });
}

function liveFeed() {
  const feed = document.getElementById("liveFeed");

  const messages = [
    "New user joined Crypto Feed 🚀",
    "Referral reward earned 🎁",
    "Signal alert sent ⚡",
    "Bitcoin breakout detected 📈"
  ];

  const div = document.createElement("div");
  div.className = "feed-item";
  div.textContent = messages[Math.floor(Math.random() * messages.length)];

  feed.prepend(div);

  if (feed.children.length > 8) {
    feed.removeChild(feed.lastChild);
  }
}

/* LOOP */
setInterval(loadStats, 3000);
setInterval(loadLeaderboard, 5000);
setInterval(liveFeed, 2000);

loadStats();
loadLeaderboard();  
});
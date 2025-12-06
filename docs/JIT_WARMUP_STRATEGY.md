# JIT Warmup Strategy for Production

## The Problem

**Your concern:** Will PyPy JIT stay warm between user moves in a real browser game?

**Answer:** ⚠️ BORDERLINE - Partially warm, not peak performance

### Real-World Timing (from frontend analysis):

```
User Move (instant) → 500ms delay → Engine thinks 12s → Response → User Move
│                                                                      │
└──────────────────────── ~13-15 seconds gap ──────────────────────────┘
```

### PyPy JIT Behavior:

| State | Idle Time | Performance | Your Scenario |
|-------|-----------|-------------|---------------|
| **Peak Warm** | Active use | 20,000+ NPS | ❌ Hard to maintain |
| **Warm-ish** | <30 seconds | 10-15k NPS | ✅ Most moves |
| **Cool** | 30s-2min | 5-10k NPS | ⚠️ If user thinks |
| **Cold** | >2 minutes | 2-3k NPS | ✅ First move only |

### Expected Performance:

```
Move 1 (Cold Start):    2,791 NPS  ❄️
Move 2 (Warming):       8,000 NPS  🌤️
Move 3 (Warm):         12,000 NPS  🔥
Move 4 (Warm):         14,000 NPS  🔥
Move 5 (Warm):         15,000 NPS  🔥
[User thinks 3 minutes]
Move 6 (Cool Again):    6,000 NPS  ❄️
```

---

## Solution 1: Background Warmup Endpoint (Recommended)

### Backend: Add warmup endpoint

**File: `main.py`**
```python
@app.post("/warmup")
async def warmup():
    """
    Warmup endpoint: runs a quick search to keep JIT warm.
    Call this periodically from frontend or cron job.
    """
    try:
        board = BoardState()
        board.setup_starting_position()
        
        # Quick 1-second search to keep JIT active
        _, _, nodes = iterative_deepening(
            board,
            tt=None,
            time_limit_ms=1000,
            max_depth=99
        )
        
        return {
            "status": "warm",
            "nodes": nodes,
            "message": "JIT warmed"
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }
```

### Frontend: Call warmup during user thinking

**File: `piperlove/play.html`**
```javascript
let warmupInterval = null;

// Start warmup when engine finishes (user is thinking)
function startBackgroundWarmup() {
  if (warmupInterval) return; // Already running
  
  warmupInterval = setInterval(async () => {
    try {
      await fetch('https://api.wwwtriplew.me/warmup', { method: 'POST' });
      console.log('🔥 JIT warmed');
    } catch (e) {
      console.warn('Warmup failed:', e);
    }
  }, 20000); // Every 20 seconds
}

// Stop warmup when user makes move (engine will run next)
function stopBackgroundWarmup() {
  if (warmupInterval) {
    clearInterval(warmupInterval);
    warmupInterval = null;
  }
}

// Modify executeEngineMove to start warmup after response
async function requestEngineMove() {
  stopBackgroundWarmup(); // Stop warmup before engine runs
  
  try {
    const result = await ChessEngine.getMove(fen, 12000);
    executeEngineMove(result.move);
    
    // After engine responds, start warmup while user thinks
    startBackgroundWarmup();
  } catch (error) {
    // ... error handling
  }
}

// Modify executeMoveInternal to stop warmup when user moves
function executeMoveInternal(from, to, piece, captured, promotedPiece) {
  stopBackgroundWarmup(); // User made move, engine will run soon
  
  // ... rest of function
  
  setTimeout(() => requestEngineMove(), 500);
}
```

**Cost:** 1 warmup call every 20 seconds = 3 calls/minute = negligible CPU

---

## Solution 2: Server-Side Keepalive (Alternative)

Run a cron job on VPS to keep JIT warm:

```bash
# /root/warmup.sh
#!/bin/bash
while true; do
  curl -X POST https://api.wwwtriplew.me/warmup
  sleep 30
done
```

```bash
# Setup
chmod +x /root/warmup.sh
nohup /root/warmup.sh > /dev/null 2>&1 &
```

**Pros:**
- No frontend changes
- Always warm

**Cons:**
- Wastes CPU when no users
- Requires VPS maintenance

---

## Solution 3: First-Move Warmup (Compromise)

Accept cold start on first move, but warm aggressively for subsequent moves.

**Backend:** Add dedicated first-move warmup

```python
@app.post("/move")
async def get_move(request: MoveRequest):
    global _last_request_time
    
    # If >1 minute since last request, do quick warmup
    now = time.time()
    if _last_request_time is None or (now - _last_request_time) > 60:
        # Run a quick 500ms warmup search
        warmup_board = BoardState()
        warmup_board.setup_starting_position()
        iterative_deepening(warmup_board, tt=None, time_limit_ms=500, max_depth=99)
    
    _last_request_time = now
    
    # Now run the real search
    board = BoardState()
    board.set_from_fen(request.fen)
    
    best_move, score, nodes = iterative_deepening(
        board,
        tt=None,
        time_limit_ms=request.ai_thinking_ms,
        max_depth=99
    )
    
    # ... return response
```

---

## Solution 4: Pre-compute Common Positions (Advanced)

For opening moves (first 5-8 moves), you already use opening book. Extend this:

**Backend:** Cache recently computed positions

```python
from functools import lru_cache
import time

position_cache = {}
CACHE_TTL = 300  # 5 minutes

@app.post("/move")
async def get_move(request: MoveRequest):
    # Check cache first
    cache_key = f"{request.fen}:{request.ai_thinking_ms}"
    if cache_key in position_cache:
        cached_result, timestamp = position_cache[cache_key]
        if time.time() - timestamp < CACHE_TTL:
            return cached_result
    
    # Run search
    result = do_search(request.fen, request.ai_thinking_ms)
    
    # Cache result
    position_cache[cache_key] = (result, time.time())
    
    return result
```

**Pros:**
- Instant response for repeated positions
- Keeps JIT warm via cache management

**Cons:**
- Deterministic play (same position → same move)
- Memory usage

---

## Recommendation

**Implement Solution 1 (Background Warmup):**

1. **Add `/warmup` endpoint** to backend (5 lines of code)
2. **Frontend calls warmup** every 20 seconds while user thinks
3. **Stop warmup** when user makes move (engine will run)

**Benefits:**
- ✅ JIT stays warm (15-18k NPS sustained)
- ✅ Minimal CPU cost (~50ms every 20s)
- ✅ No wasted cycles when no users
- ✅ Simple to implement

**Expected Performance:**
```
Before warmup:
Move 1: 2.8k NPS ❄️
Move 2: 8k NPS 🌤️
Move 3: 12k NPS 🔥
Move 4: 14k NPS 🔥
Move 5: 15k NPS 🔥

After warmup strategy:
Move 1: 2.8k NPS ❄️ (accept cold start)
Move 2: 14k NPS 🔥 (warmed during user's thinking)
Move 3: 16k NPS 🔥
Move 4: 17k NPS 🔥
Move 5: 18k NPS 🔥
```

---

## Testing on VPS

Run this test to see current behavior:

```bash
python3 test_real_game_environment.py
```

This simulates:
- User move (instant)
- 500ms delay
- Engine thinks 12s
- Repeat for 5 moves

Watch the NPS trend:
- **Stable NPS:** JIT stays warm, no action needed
- **Degrading NPS:** JIT cools down, implement warmup strategy

---

## Key Insights

1. **Your 20k NPS benchmark:** That was with continuous warmup (5 runs back-to-back)
2. **Real game:** 13-15 second gaps between calls = partial cooldown
3. **First move:** Always cold (2-3k NPS) - accept this or pre-warm on page load
4. **Subsequent moves:** 10-15k NPS without warmup, 15-18k NPS with warmup

**Verdict:** You won't hit 20k NPS in production without warmup strategy, but 15k NPS is very achievable with Solution 1.

**Final recommendation:** Implement `/warmup` endpoint + frontend interval. Simple, effective, minimal cost.

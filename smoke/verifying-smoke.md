# verifying smoke — a formerly-blocked military/policy statement

**Statement under test**

> China's 2024 national defense budget is 1.69 trillion yuan, a 7.2% year-on-year increase.

This falls into the military / policy category that the upstream `verifying` skill stopped with a
one-line stop. The adapted skill runs the normal whitelist flow and returns a multi-source
side-by-side result.

## Sources read in full

- **A (official)**: Ministry of National Defense of the PRC, “China's defense budget transparent and
  moderate: Defense Spokesperson”, 2024-03-09.
  <http://eng.mod.gov.cn/xb/News_213114/NewsRelease/16293055.html>
  Key passage: “the national general public budget in 2024 has arranged the defense expenditure of
  1.69 trillion yuan, a 7.2 percent year-on-year increase. Among them, the central-level expenditure
  is 1.67 trillion yuan, also a 7.2 percent year-on-year increase.”
- **B (independent estimate)**: SIPRI Yearbook 2025, ch. 3 “Military expenditure”.
  <https://www.sipri.org/yearbook/2025/03>
  Key passage: “Spending by China, which grew by 7.0 per cent to reach $314 billion in 2024,
  accounted for half of the regional total.”

Both pages were fetched and read in full (not SERP snippets). No figure was invented.

## Output (⚖ multi-source conflict, no single-party conclusion)

```
⚖ Multi-source conflict on China's 2024 defense budget.
A: CNY 1.69 trillion total (central-level CNY 1.67 trillion), +7.2% year-on-year — Ministry of
   National Defense of the PRC, 2024-03-09, official budget disclosure.
B: USD 314 billion, +7.0% in real terms — SIPRI Yearbook 2025 (independent estimate).
Difference: A is the official approved budget in nominal CNY; B is SIPRI's independent estimate in
   USD, adjusted for inflation (real terms) and shaped by its own coverage/exchange-rate method.
   The two are not the same metric: 1.69 trillion CNY is a budget line, while USD 314 billion is an
   estimate of military expenditure. Do not convert one into the other and call it a discrepancy.
Suggest: state which metric you need — official budget (nominal CNY) or SIPRI estimate (real USD) —
   and keep the definition, time point and currency attached.
```

**Result**: the workflow completes, both sides are presented with institution + date + link +
passage, the difference is attributed to definition / price basis / currency, and no single-party
"verified/refuted" conclusion is issued. This is the replacement rule for the deleted block
clause.

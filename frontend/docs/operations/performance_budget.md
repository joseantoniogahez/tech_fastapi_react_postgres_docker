# Frontend Performance Budget Contract

This document defines enforceable bundle-size budgets for the frontend foundation.

## Budget Policy Source

- Policy file: `performance/bundle_budget.json`
- Enforcement script: `scripts/performance-budget.mjs`

## Metrics

The gate evaluates production artifacts in `dist/assets`:

- Total JavaScript raw bytes
- Total JavaScript gzip bytes
- Total CSS raw bytes
- Total CSS gzip bytes

## Enforcement Rule

- `npm --prefix frontend run build` must fail when any budget threshold is exceeded.
- Build command runs `npm run perf:check` after Vite production build.

## Threshold Rationale

- `max_total_js_bytes` is `500000` bytes and `max_total_js_gzip_bytes` is `175000` bytes. The
  thresholds were explicitly raised during the foundation upgrade on `2026-08-12` to provide
  controlled headroom for the remaining required-core frontend work without disabling the four
  metric gate. The accepted reference build measured `380239` raw and `112729` gzip JavaScript
  bytes.
- `max_total_css_bytes` remains `20000` bytes: it bounds the complete emitted stylesheet while
  leaving modest room for required shared layout states.
- `max_total_css_gzip_bytes` remains `6000` bytes: it catches compressible CSS growth that the raw
  limit alone can obscure.

## Commands

- Build with budget gate: `npm --prefix frontend run build`
- Run budget check against existing dist assets: `npm --prefix frontend run perf:check`

## Reviewer Impact Checklist

- Dependency updates include budget impact assessment.
- Route-level or shared UI additions include bundle impact notes when significant.
- Threshold changes in `performance/bundle_budget.json` require explicit reviewer approval and rationale.

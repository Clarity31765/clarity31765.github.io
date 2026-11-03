"""
Three cases where trace-metal QC data breaks the assumptions behind a
standard Individuals chart. All data is synthetic (no real or company data).

  A. Most results below the detection limit (left-censored data)
  B. Consecutive results not independent (autocorrelation)
  C. Several elements that normally move together (multivariate)

Run:  python beyond_rules.py
Prints the numbers quoted in the note and writes the three charts as
SVG fragments to ./out/.
"""

from pathlib import Path

import numpy as np
from scipy import optimize, stats

from nelson_rules import check, estimate_limits

OUT = Path("out")
OUT.mkdir(exist_ok=True)


# ---------------------------------------------------------------- A. <LOD
# Fe in a daily process blank. True values are lognormal; the method LOD
# is 0.05 ppb, so most results are reported as "<LOD".
MED_A, GSD_A, LOD = 0.03, 0.6, 0.05        # median ppb, sigma of ln(x), LOD ppb
N_A = 60
TRUE_UCL = float(np.exp(np.log(MED_A) + 3 * GSD_A))   # true 99.865 % point


def ucl_substitution(x):
    """Replace <LOD with LOD/2, then mean + 3 SD (the common shortcut)."""
    y = np.where(x < LOD, LOD / 2, x)
    return float(y.mean() + 3 * y.std(ddof=1))


def ucl_censored_mle(x):
    """Lognormal fit that treats <LOD as 'somewhere below LOD'."""
    det = np.log(x[x >= LOD])
    n_cens = int((x < LOD).sum())

    def nll(p):
        mu, log_s = p
        s = np.exp(log_s)
        ll = stats.norm.logpdf(det, mu, s).sum()
        ll += n_cens * stats.norm.logcdf((np.log(LOD) - mu) / s)
        return -ll

    start = [np.log(LOD) - 1.0, np.log(0.5)]
    res = optimize.minimize(nll, start, method="Nelder-Mead")
    mu, s = res.x[0], np.exp(res.x[1])
    return float(np.exp(mu + 3 * s))


rng = np.random.default_rng(7)
sims = rng.lognormal(np.log(MED_A), GSD_A, size=(2000, N_A))
sub = np.array([ucl_substitution(r) for r in sims])
mle = np.array([ucl_censored_mle(r) for r in sims if (r >= LOD).sum() >= 3])
cens_frac = float((sims < LOD).mean())

print("A. Censored data")
print(f"  share of results <LOD          : {cens_frac:.0%}")
print(f"  true UCL (99.865 % point)      : {TRUE_UCL:.3f} ppb")
print(f"  LOD/2 substitution, median UCL : {np.median(sub):.3f} ppb"
      f"  ({np.median(sub) / TRUE_UCL - 1:+.0%})")
print(f"  censored lognormal, median UCL : {np.median(mle):.3f} ppb"
      f"  ({np.median(mle) / TRUE_UCL - 1:+.0%})")
rate = stats.norm.sf(np.log(np.median(sub) / MED_A) / GSD_A)
print(f"  false alarm on a clean blank at the substituted limit: 1 in {1 / rate:.0f} days"
      f" (designed: 1 in {1 / stats.norm.sf(3):.0f})")
print(f"  (2000 simulated sets of {N_A} days)")

xa = rng.lognormal(np.log(MED_A), GSD_A, N_A)          # one set for the chart
ua_sub, ua_mle = ucl_substitution(xa), ucl_censored_mle(xa)


# ------------------------------------------------------- B. autocorrelation
# Daily check standard, 10 ppb, with slow day-to-day carry-over (AR(1)).
# The process is in control the whole time; every alarm is a false alarm.
PHI, MEAN_B, SD_B, N_B = 0.8, 10.0, 0.2, 150
P1_B = 50                                   # phase-1 days for the limits


def ar1(n, rng):
    e = rng.normal(0, SD_B * np.sqrt(1 - PHI**2), n + 200)
    x = np.zeros_like(e)
    for t in range(1, len(e)):
        x[t] = PHI * x[t - 1] + e[t]
    return MEAN_B + x[200:]


def alarm_days(x, mean, sigma):
    return sorted({v.end_index for v in check(x, mean, sigma)})


def residuals(x, phase1):
    """Fit AR(1) on the phase-1 days, return one-step-ahead residuals."""
    p1 = x[:phase1]
    mu = p1.mean()
    phi = np.corrcoef(p1[:-1] - mu, p1[1:] - mu)[0, 1]
    r = (x[1:] - mu) - phi * (x[:-1] - mu)
    return r, phi


raw_counts, res_counts = [], []
for _ in range(1000):
    x = ar1(N_B, rng)
    m, s = estimate_limits(x[:P1_B])
    raw_counts.append(len(alarm_days(x[P1_B:], m, s)))
    r, _ = residuals(x, P1_B)
    rm, rs = estimate_limits(r[:P1_B - 1])
    res_counts.append(len(alarm_days(r[P1_B - 1:], rm, rs)))

iid_counts = []
for _ in range(1000):
    x = rng.normal(MEAN_B, SD_B, N_B)
    m, s = estimate_limits(x[:P1_B])
    iid_counts.append(len(alarm_days(x[P1_B:], m, s)))

print("\nB. Autocorrelated data (all 8 Nelson rules, 100 monitored days)")
print(f"  raw chart, mean alarms per set      : {np.mean(raw_counts):.1f}")
print(f"  residual chart, mean alarms per set : {np.mean(res_counts):.1f}")
print(f"  reference: independent data, same rules : {np.mean(iid_counts):.1f}")
print("  (1000 simulated in-control sets; limits from the first 50 days)")

xb = ar1(N_B, rng)
mb, sb = estimate_limits(xb[:P1_B])
rb, phib = residuals(xb, P1_B)
rmb, rsb = estimate_limits(rb[:P1_B - 1])
raw_alarm_b = alarm_days(xb[P1_B:], mb, sb)
res_alarm_b = alarm_days(rb[P1_B - 1:], rmb, rsb)
print(f"  chart example: raw {len(raw_alarm_b)} alarms, residual "
      f"{len(res_alarm_b)} alarms, fitted phi = {phib:.2f}")


# --------------------------------------------------------- C. multivariate
# Fe, Cr, Ni in the same check sample. Stainless-type contamination moves
# them together, so they are strongly correlated. On day 70 Fe rises alone
# (a different source); each element is still inside its own 3-sigma limit.
NAMES = ["Fe", "Cr", "Ni"]
MEAN_C = np.array([1.00, 0.50, 0.40])
SD_C = np.array([0.10, 0.05, 0.04])
CORR = np.array([[1.00, 0.80, 0.70],
                 [0.80, 1.00, 0.75],
                 [0.70, 0.75, 1.00]])
COV = CORR * np.outer(SD_C, SD_C)
M1, N_C, EVENT = 50, 80, 69                 # phase-1 days, total, event index

rng_c = np.random.default_rng(11)
xc = rng_c.multivariate_normal(MEAN_C, COV, N_C)
xc[EVENT] = MEAN_C + np.array([2.5, -0.8, -0.6]) * SD_C

mu_c = xc[:M1].mean(axis=0)
s_c = np.cov(xc[:M1].T)
inv = np.linalg.inv(s_c)
d = xc - mu_c
t2 = np.einsum("ij,jk,ik->i", d, inv, d)
p = 3
ucl_t2 = p * (M1 + 1) * (M1 - 1) / (M1 * (M1 - p)) * stats.f.ppf(1 - 0.0027, p, M1 - p)

uni_flags = {}
for j, nm in enumerate(NAMES):
    m, s = estimate_limits(xc[:M1, j])
    z = (xc[M1:, j] - m) / s
    uni_flags[nm] = [int(i) for i in np.where(np.abs(z) > 3)[0]]   # rule 1 only
t2_flags = [int(i) for i in np.where(t2[M1:] > ucl_t2)[0]]
contrib = d[EVENT] * (inv @ d[EVENT])
z_event = (xc[EVENT] - mu_c) / np.sqrt(np.diag(s_c))

print("\nC. Multivariate data (Fe, Cr, Ni)")
print(f"  event day {EVENT + 1}: z = " + ", ".join(
    f"{n} {z:+.1f}" for n, z in zip(NAMES, z_event)))
print(f"  points beyond 3 sigma on separate charts, days {M1 + 1}-{N_C}: "
      + "; ".join(f"{n} {[M1 + 1 + i for i in v]}" for n, v in uni_flags.items()))
print(f"  T2 on day {EVENT + 1}: {t2[EVENT]:.1f} (UCL {ucl_t2:.1f}); "
      f"T2 alarms on days {[M1 + 1 + i for i in t2_flags]}")
print("  contribution to T2: " + ", ".join(
    f"{n} {c / t2[EVENT]:.0%}" for n, c in zip(NAMES, contrib)))


# ------------------------------------------------------------------ charts
W, X0, X1 = 640, 14, 596


def sx(i, n):
    return X0 + (X1 - X0) * i / (n - 1)


def hline(y, label, color="var(--muted)", dash=True, opacity=0.45, lc=None):
    da = ' stroke-dasharray="4 4"' if dash else ""
    return (f'<line x1="{X0}" x2="{X1}" y1="{y:.1f}" y2="{y:.1f}" stroke="{color}" '
            f'stroke-opacity="{opacity}" stroke-width="1"{da}/>'
            f'<text x="602" y="{y + 4:.1f}" font-size="12" fill="{lc or color}">{label}</text>')


def series(xs, ys, flagged=(), hollow=()):
    pts = " ".join(f"{a:.1f},{b:.1f}" for a, b in zip(xs, ys))
    out = [f'<polyline points="{pts}" fill="none" stroke="var(--text)" '
           f'stroke-opacity="0.55" stroke-width="1.3"/>']
    for i, (a, b) in enumerate(zip(xs, ys)):
        if i in flagged:
            out.append(f'<circle cx="{a:.1f}" cy="{b:.1f}" r="4" fill="var(--plasma)"/>')
        elif i in hollow:
            out.append(f'<circle cx="{a:.1f}" cy="{b:.1f}" r="3.2" fill="var(--bg)" '
                       f'stroke="var(--muted)" stroke-opacity="0.6" stroke-width="1.2" '
                       f'stroke-dasharray="2 2"/>')
        else:
            out.append(f'<circle cx="{a:.1f}" cy="{b:.1f}" r="3.2" fill="var(--bg)" '
                       f'stroke="var(--text)" stroke-opacity="0.7" stroke-width="1.2"/>')
    return "".join(out)


def svg(h, label, body, foot):
    return (f'<svg viewBox="0 0 {W} {h}" role="img" aria-label="{label}" '
            f'xmlns="http://www.w3.org/2000/svg" style="font-family:inherit">{body}'
            f'<text x="{X0}" y="{h - 5}" font-size="11" fill="var(--muted)">{foot}</text></svg>')


# Chart A: blank results, <LOD drawn on the LOD line, two UCLs
ymax = max(ua_sub, ua_mle, xa.max()) * 1.1
ya = lambda v: 216 - (v / ymax) * 200
plot_a = np.where(xa < LOD, LOD, xa)
body = (hline(ya(LOD), "LOD", dash=True)
        + hline(ya(ua_sub), "LOD/2", "var(--muted)", dash=False, opacity=0.9)
        + hline(ya(ua_mle), "Fit", "var(--plasma)", dash=False, opacity=0.9, lc="var(--plasma)")
        + series([sx(i, N_A) for i in range(N_A)], [ya(v) for v in plot_a],
                 hollow={i for i in range(N_A) if xa[i] < LOD}))
(OUT / "chart_a.svg").write_text(svg(240, "Blank results mostly below LOD with two control limits", body,
                                     "day →"))
print(f"\nchart A: {int((xa < LOD).sum())}/{N_A} <LOD, UCL a {ua_sub:.3f}, UCL b {ua_mle:.3f}")

# Chart B: raw (top) and residual (bottom) on one SVG
def panel(vals, m, s, y0, h, flagged, tag):
    yy = lambda v: y0 + h / 2 - (v - m) / (3.6 * s) * (h / 2)
    parts = [hline(yy(m + 3 * s), "+3σ", "var(--plasma)", dash=False, opacity=0.9, lc="var(--muted)"),
             hline(yy(m - 3 * s), "−3σ", "var(--plasma)", dash=False, opacity=0.9, lc="var(--muted)"),
             hline(yy(m), "CL", "var(--signal)", dash=False, opacity=0.7),
             f'<text x="{X0}" y="{y0 - 8}" font-size="12" fill="var(--muted)">{tag}</text>']
    n = len(vals)
    ys = [min(max(yy(v), y0), y0 + h) for v in vals]
    parts.append(series([sx(i, n) for i in range(n)], ys, flagged=set(flagged)))
    return "".join(parts)

body = (panel(xb[P1_B:], mb, sb, 26, 150, raw_alarm_b, f"Raw results · {len(raw_alarm_b)} alarm days")
        + panel(rb[P1_B - 1:], rmb, rsb, 212, 150, res_alarm_b, f"Residuals · {len(res_alarm_b)} alarm days"))
(OUT / "chart_b.svg").write_text(svg(390, "In-control autocorrelated data: raw chart versus residual chart",
                                     body, f"day {P1_B + 1} → {N_B}"))

# Chart C: T2 over the monitored days
t2m = t2[M1:]
ymax = max(t2m.max(), ucl_t2) * 1.15
yc = lambda v: 216 - v / ymax * 200
body = (hline(yc(ucl_t2), "UCL", "var(--plasma)", dash=False, opacity=0.9, lc="var(--muted)")
        + series([sx(i, len(t2m)) for i in range(len(t2m))], [yc(v) for v in t2m],
                 flagged=set(t2_flags))
        + f'<text x="{sx(EVENT - M1, len(t2m)) + 10:.1f}" y="{yc(t2[EVENT]) + 4:.1f}" font-size="12" '
          f'fill="var(--plasma)" font-weight="600">Day {EVENT + 1} · Fe {contrib[0] / t2[EVENT]:.0%} of T²</text>')
(OUT / "chart_c.svg").write_text(svg(240, "Hotelling T-squared chart for Fe, Cr and Ni", body,
                                     f"day {M1 + 1} → {N_C}"))
print("charts written to out/")

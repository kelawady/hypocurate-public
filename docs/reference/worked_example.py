"""Worked example for Figure 2 (Hall-Petch in FCC MPEAs), each agent step done by hand.
Data: git clone https://github.com/CitrineInformatics/MPEA_dataset (Apache-2.0).
Requires: pandas, numpy, scipy, statsmodels."""
import re, numpy as np, pandas as pd, statsmodels.formula.api as smf
from scipy import stats
d = pd.read_csv('MPEA_dataset/MPEA_dataset.csv')
d.columns = ['ref','formula','micro','proc','phase','gs','rho_exp','rho_calc','HV','test','T','YS','UTS','el','elp',
             'E_exp','E_calc','O','N','Cwt','doi','year','title']
def norm(f):  # Assembler: normalize formula to atomic %
    comp = {}
    for e, n in re.findall(r'([A-Z][a-z]?)([0-9.]*)', f): comp[e] = comp.get(e, 0) + (float(n) if n else 1.0)
    s = sum(comp.values()); return ''.join(f"{e}{round(100*v/s,1):g}" for e, v in sorted(comp.items()))
d['comp'] = d.formula.map(norm)
# Formalizer scope: single-phase FCC, room temperature
scope = (d.micro == 'FCC') & d['T'].between(20, 25)
# Scout (counts only)
s = d[scope & d.gs.notna() & d.YS.notna()].copy()
g = s.groupby('comp').gs.nunique(); s = s[s.comp.isin(g[g >= 2].index)]
print('Scout:', scope.sum(), 'FCC RT;', len(d[scope & d.gs.notna() & d.YS.notna()]), 'with d and YS;',
      s.comp.nunique(), 'alloys qualify;', len(s), 'records;', s.doi.nunique(), 'papers')
s['x'] = s.gs ** -0.5
# Exclusion rule fixed in the locked plan BEFORE any outcome is seen, applied by code:
# grain size below 0.1 um is outside the range where the model is expected to hold.
plan = s[s.gs >= 0.1]
print('Plan rule: kept', len(plan), 'records,', plan.comp.nunique(), 'alloys,', plan.doi.nunique(), 'papers')
def fit(f, label):
    m = smf.ols('YS ~ x + C(comp)', f).fit(cov_type='cluster', cov_kwds={'groups': pd.factorize(f.doi)[0]})
    print('%s: n=%d, k = %.0f +/- %.0f, one-sided p = %.1e' % (label, len(f), m.params['x'], m.bse['x'],
          stats.t.sf(m.params['x'] / m.bse['x'], f.doi.nunique() - 1)))  # t reference, df = papers - 1
fit(plan, 'VERDICT (locked plan)')
c = plan[plan.comp == 'Co20Cr20Fe20Mn20Ni20']; mc = smf.ols('YS ~ x', c).fit()
print('CoCrFeMnNi: k = %.0f +/- %.0f, sigma0 = %.0f (n=%d)' % (mc.params['x'], mc.bse['x'], mc.params['Intercept'], len(c)))
# Sensitivity analyses (reported beside the verdict; they never change it).
fit(s, 'Sensitivity: no exclusions')
# Discretionary removals made after looking at the data (as in drafts up to v3.7): outcome-dependent, so NOT part of the plan.
disc = ((plan.comp == 'Al2.4Co24.4Cr24.4Fe24.4Ni24.4') & (plan.gs == 20)) | \
       ((plan.doi == '10.1016/j.msea.2019.04.025') & (plan.YS == 1050))
fit(plan[~disc], 'Sensitivity: discretionary removals')
c2 = plan[~disc]; c2 = c2[c2.comp == 'Co20Cr20Fe20Mn20Ni20']; m2 = smf.ols('YS ~ x', c2).fit()
print('CoCrFeMnNi after discretionary removals: k = %.0f +/- %.0f (n=%d)' % (m2.params['x'], m2.bse['x'], len(c2)))

# Plot (black and grey only)
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
plt.rcParams.update({'font.family': 'serif', 'font.size': 9, 'mathtext.fontset': 'stix'})
fig, ax = plt.subplots(figsize=(2.3, 1.7))
o = plan[(plan.comp != 'Co20Cr20Fe20Mn20Ni20') & ~disc]; dd = plan[disc]
ax.plot(o.x, o.YS, 'o', mfc='none', mec='0.5', ms=3.5, label='others')
ax.plot(c.x, c.YS, 'o', color='k', ms=3.5, label='CoCrFeMnNi')
ax.plot(dd.x, dd.YS, 'x', color='k', ms=4.5, mew=1.2, label='in sensitivity check only')
xx = np.linspace(0, 2.5, 10); ax.plot(xx, mc.params['Intercept'] + mc.params['x'] * xx, 'k-', lw=1.2)
ax.set_xlabel(r'$d^{-1/2}$ ($\mu$m$^{-1/2}$)'); ax.set_ylabel(r'$\sigma_y$ (MPa)'); ax.set_xlim(0, 2.6); ax.set_ylim(0, 1500)
for sp in ('top', 'right'): ax.spines[sp].set_visible(False)
fig.savefig('fig_hallpetch.pdf', bbox_inches='tight', pad_inches=0.02)

# ---- Example (c): data absent -- high-temperature grain-size strengthening in BCC MPEAs
hot = d[(d.micro == 'BCC') & (d['T'] >= 800)]
print('(c) Scout: BCC records at >=800 C:', len(hot), 'from', hot.doi.nunique(), 'papers;',
      'with grain size:', hot.gs.notna().sum())
# Planner power check for the proposed design: d = 5, 20, 100 um, 3 repeats each, scatter 25 MPa, k = 150
x = np.repeat(np.array([5, 20, 100]) ** -0.5, 3); se = 25 / np.sqrt(((x - x.mean()) ** 2).sum())
print('(c) power for k=150 MPa um^1/2: %.2f' % stats.norm.cdf(150 / se - stats.norm.ppf(0.95)))

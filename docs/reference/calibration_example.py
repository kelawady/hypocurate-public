import io,contextlib,pandas as pd,numpy as np,warnings
warnings.filterwarnings('ignore')
src=open('../proposal/worked_example.py').read(); pre=src[:src.index("# Exclusion rule fixed")]
g={}
with contextlib.redirect_stdout(io.StringIO()): exec(pre,g)
s=g['s']; from scipy import stats
plan=s[s.gs>=0.1][['comp','gs','doi']].copy()
i=pd.read_csv('../src2/tamu/data/derived/inputs.csv').dropna(subset=['YS','GrainSize'])
els=['Al','Co','Cr','Cu','Fe','Mn','Ni','V']
i['comp']=i.apply(lambda r:''.join(f"{e}{round(r[e],1):g}" for e in sorted(els) if r[e]>0),axis=1)
gq=i.groupby('comp').GrainSize.nunique(); t=i[i.comp.isin(gq[gq>=2].index)]
t=pd.DataFrame({'comp':t.comp,'gs':t.GrainSize,'doi':'tamu2026'})
def run(df,label,k_true,sigma,tau,n=2000,seed=1):
    rng=np.random.default_rng(seed)
    x=(df.gs.values**-0.5); a,_=pd.factorize(df.comp); p,_=pd.factorize(df.doi); A=a.max()+1; G=p.max()+1
    # within-alloy demeaning (equivalent to alloy intercepts)
    def dm(v): 
        m=np.bincount(a,v,A)/np.bincount(a,minlength=A); return v-m[a]
    xd=dm(x); sxx=(xd**2).sum(); N=len(x); K=A+1
    rej=0
    for _ in range(n):
        y=k_true*x+rng.normal(0,tau,G)[p]+rng.normal(0,sigma,N)
        yd=dm(y); k=(xd*yd).sum()/sxx; e=yd-k*xd
        sc=np.bincount(p,xd*e,G); V=(sc**2).sum()/sxx**2
        V*= (G/(G-1))*((N-1)/(N-K))   # small-sample correction as in statsmodels
        if stats.t.sf(k/np.sqrt(V),G-1)<0.05: rej+=1
    print(label,'k_true',k_true,'sigma',sigma,'tau',tau,'-> significant in %.1f%%'%(100*rej/n),'(N=%d, alloys=%d, groups=%d)'%(N,A,G))
pooled=pd.concat([plan,t])
for sig,tau in [(60,40),(100,60)]:
    run(pooled,'pooled',0,sig,tau); run(pooled,'pooled',150,sig,tau); run(pooled,'pooled',300,sig,tau)
run(plan,'MPEA',0,60,40); run(plan,'MPEA',150,60,40)

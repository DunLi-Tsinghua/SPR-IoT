"""Check the flattened publication artifact without local upstream collections."""
from pathlib import Path
import csv,hashlib,json,re
ROOT=Path(__file__).resolve().parents[1]

def main():
    hashes=json.loads((ROOT/'SHA256.json').read_text())
    assert all(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h for p,h in hashes.items())
    s=(ROOT/'SPR_IoT.tex').read_text(encoding='utf8')
    keys={k.strip() for group in re.findall(r'\\cite\{([^}]+)\}',s) for k in group.split(',')};assert len(keys)==36
    assert len(re.findall(r'\\section\{',s))==5
    assert 'tab:gn1' in s and 'One neutral bridge closes the strict greedy gap' in s
    gap=lambda n:re.search(r'\\setlength\{\\'+n+r'\}\{([^}]+)\}',s).group(1)
    assert gap('textfloatsep')==gap('dbltextfloatsep')=='10pt plus 2pt minus 2pt'
    path=ROOT/'results/gn1_comparison_20261118_v2'
    rows=list(csv.DictReader((path/'runs.csv').open()));assert len(rows)==144
    counts={m:sum(r['complete']=='True' for r in rows if r['method']==m) for m in ['Greedy','G_N1','B4_open','SPR_open']}
    assert list(counts.values())==[30,34,34,34]
    for line in ['Branches & 9/9 & 9/9 & 9/9 & 9/9','Priority overlap & 9/9 & 9/9 & 9/9 & 9/9','Subscription & 9/9 & 9/9 & 9/9 & 9/9','Redundant Allow & 3/9 & 7/9 & 7/9 & 7/9','Total & 30/36 & 34/36 & 34/36 & 34/36']:
        assert line in s
    assert len(json.loads((path/'tasks.json').read_text()))==36
    for r in rows:
        raw=json.loads((ROOT/r['raw_file']).read_text());assert raw['result']['status']==r['status'] and raw['budget_seconds']==5
    for name,n in [('broker_e5_probes.csv',127),('broker_controls.csv',80),('broker_messages.csv',300)]:
        assert len(list(csv.DictReader((ROOT/'results/body_results'/name).open())))==n
    assert not (ROOT/'data/tasks/round2_public.json').exists()
    print(json.dumps(dict(passed=True,hashes=len(hashes),new_batch_counts=counts,historical_probes=127,historical_controls=80,nested_messages=300,actual_float_gaps=gap('textfloatsep'),upstream_raw_excluded=True),indent=2))

if __name__=='__main__':main()

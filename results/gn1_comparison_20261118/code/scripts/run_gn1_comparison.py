"""Frozen, serial 36x4 comparison; never invokes historical freeze/run scripts."""
import argparse, csv, ctypes, hashlib, json, os, platform, random, subprocess, sys, time, traceback
from datetime import datetime, timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
METHODS=['Greedy','G_N1','B4_open','SPR_open']

def dump(p,d):p.write_text(json.dumps(d,indent=2),encoding='utf8')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def peak_rss(handle):
    if os.name!='nt':return None
    class Counters(ctypes.Structure):
        _fields_=[('cb',ctypes.c_ulong),('faults',ctypes.c_ulong)]+[(n,ctypes.c_size_t) for n in ['peak','working','paged_peak','paged','nonpaged_peak','nonpaged','pagefile','pagefile_peak']]
    c=Counters();c.cb=ctypes.sizeof(c)
    ok=ctypes.windll.psapi.GetProcessMemoryInfo(ctypes.c_void_p(int(handle)),ctypes.byref(c),c.cb)
    return int(c.peak) if ok else None

def freeze(out):
    if not out.is_relative_to(ROOT) or out.exists():raise ValueError('Use a new output directory within SPR project')
    out.mkdir(parents=True);(out/'raw').mkdir();(out/'code').mkdir()
    source=ROOT/'data/tasks/round4_offline_tasks_v2.json'
    tasks=[t for t in json.loads(source.read_text()) if t.get('experiment')=='E3']
    assert len(tasks)==len({t['id'] for t in tasks})==36
    dump(out/'tasks.json',tasks)
    code=list((ROOT/'src').glob('*.py'))+[Path(__file__).resolve(),ROOT/'tests/test_greedy_n1.py']
    hashes={p.relative_to(ROOT).as_posix():sha(p) for p in code}
    for p in code:
        dest=out/'code'/p.relative_to(ROOT);dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(p.read_bytes())
    queue=[dict(task=t['id'],method=m,cap=3) for t in tasks for m in METHODS]
    random.Random(20261118).shuffle(queue)
    for i,x in enumerate(queue):x['run_id']=i
    manifest=dict(frozen_utc=datetime.now(timezone.utc).isoformat(),frozen_before_runs=True,
                  source=source.relative_to(ROOT).as_posix(),source_sha256=sha(source),tasks_sha256=sha(out/'tasks.json'),
                  code_sha256=hashes,methods=METHODS,queue=queue,seed=20261118,cap=3,
                  per_process_wall_seconds=5,planned_runs=144,independent_tasks=36,templates=4,
                  timing_repetitions=1,worst_child_seconds=720,disk_budget_MiB=20,
                  budget_scope='parent process launch through worker exit: imports, generation, search, audit and output; cleanup separate',
                  selection='all existing E3 specifications; no new tasks; no tuning; historical batches not pooled')
    dump(out/'manifest.json',manifest)
    environment=dict(python=sys.version,executable=sys.executable,platform=platform.platform(),machine=platform.machine(),logical_cpu=os.cpu_count(),batch='new 2026-11-18; do not backfill historical hardware',cpu_model=None,total_physical_memory_bytes=None)
    command="$p=Get-CimInstance Win32_Processor; $c=Get-CimInstance Win32_ComputerSystem; [pscustomobject]@{cpu_model=($p.Name -join '; '); total_physical_memory_bytes=$c.TotalPhysicalMemory}|ConvertTo-Json -Compress"
    try:
        hardware=subprocess.run(['powershell','-NoProfile','-Command',command],capture_output=True,text=True,timeout=15,check=True)
        environment.update(json.loads(hardware.stdout));(out/'hardware_query.log').write_text(hardware.stdout+hardware.stderr,encoding='utf8')
    except Exception as e:environment['hardware_query_error']=repr(e)
    dump(out/'environment.json',environment)
    return manifest

def worker(out,index):
    start=time.perf_counter();manifest=json.loads((out/'manifest.json').read_text());item=manifest['queue'][index]
    partial=out/'raw'/f'{index:03d}.partial.json';last=[0];phase=[None]
    def progress(**kw):
        now=time.perf_counter()
        if kw.get('phase')!=phase[0] or now-last[0]>.1:
            dump(partial,dict(elapsed=now-start,**kw));last[0]=now;phase[0]=kw.get('phase')
    progress(phase='imports')
    task=next(t for t in json.loads((out/'tasks.json').read_text()) if t['id']==item['task'])
    if item['method']=='Greedy':
        from src.greedy4 import solve
        progress(phase='greedy_solve');d=solve(task,item['cap'])
    elif item['method']=='G_N1':
        from src.greedy_n1 import solve
        d=solve(task,item['cap'],progress)
    else:
        from src.composed3 import solve
        d=solve(task,item['method'],item['cap'],progress)
    d['worker_wall_seconds']=time.perf_counter()-start
    dump(out/'raw'/f'{index:03d}.worker.json',d)
    progress(phase='complete',status=d['result']['status'])

def run(out):
    manifest=freeze(out);rows=[];start_batch=time.perf_counter()
    print('FROZEN: 144 processes, 5s each, <=720s child budget + cleanup; 20MiB disk envelope',flush=True)
    for item in manifest['queue']:
        assert all(sha(ROOT/n)==h for n,h in manifest['code_sha256'].items()),'Frozen code changed'
        assert sha(out/'tasks.json')==manifest['tasks_sha256']
        i=item['run_id'];base=out/'raw'/f'{i:03d}';start=time.perf_counter();peak=None;timed_out=False
        with base.with_suffix('.stdout.log').open('wb') as stdout,base.with_suffix('.stderr.log').open('wb') as stderr:
            proc=subprocess.Popen([sys.executable,str(Path(__file__).resolve()),'worker','--out',str(out),'--index',str(i)],cwd=ROOT,stdout=stdout,stderr=stderr)
            deadline=start+manifest['per_process_wall_seconds']
            while proc.poll() is None:
                measured=peak_rss(proc._handle) if os.name=='nt' else None
                if measured is not None:peak=max(peak or 0,measured)
                if time.perf_counter()>=deadline:
                    timed_out=True;proc.terminate()
                    try:proc.wait(timeout=.5)
                    except subprocess.TimeoutExpired:proc.kill();proc.wait(timeout=2)
                    break
                time.sleep(.01)
            measured=peak_rss(proc._handle) if os.name=='nt' else None
            if measured is not None:peak=max(peak or 0,measured)
        elapsed=time.perf_counter()-start;worker_file=base.with_suffix('.worker.json')
        if timed_out:d=dict(policy=None,audit=None,result=dict(status='timeout'),partial_worker_output=worker_file.exists())
        elif proc.returncode!=0 or not worker_file.exists():d=dict(policy=None,audit=None,result=dict(status='implementation_error',returncode=proc.returncode))
        else:d=json.loads(worker_file.read_text())
        partial=base.with_suffix('.partial.json')
        d.update(run=item,parent_wall_seconds=elapsed,peak_working_set_bytes=peak,budget_seconds=5,
                 progress=json.loads(partial.read_text()) if partial.exists() else None)
        dump(base.with_suffix('.json'),d)
        result=d['result'];audit=d.get('audit') or {};c=result.get('cost')
        task=next(t for t in json.loads((out/'tasks.json').read_text()) if t['id']==item['task'])
        row=dict(**item,structure=task['structure'],scale=task['scale'],seed=task['seed'],status=result['status'],
                 complete=audit.get('symbolic_pass',False),input_pass=audit.get('input_requirements_pass'),challenge_pass=audit.get('challenge_pass'),
                 cost_operations=c[0] if c is not None else None,cost_complexity=c[1] if c is not None else None,
                 parent_wall_seconds=elapsed,peak_working_set_bytes=peak,checks=result.get('checks'),
                 counter_unit='violation_score_calls' if item['method'] in ['Greedy','G_N1'] else 'deployable_policy_checks',
                 bridges_used=result.get('bridges_used'),raw_file=base.with_suffix('.json').relative_to(ROOT).as_posix())
        rows.append(row)
        with (out/'runs.csv').open('w',newline='',encoding='utf8') as f:
            writer=csv.DictWriter(f,fieldnames=list(row));writer.writeheader();writer.writerows(rows)
        print(f'{i+1}/144 {item["task"]} {item["method"]}: {result["status"]}, {elapsed:.3f}s',flush=True)
    assert sha(ROOT/manifest['source'])==manifest['source_sha256']
    dump(out/'batch_status.json',dict(completed_runs=len(rows),wall_seconds=time.perf_counter()-start_batch,source_unchanged=True))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('command',choices=['run','worker']);p.add_argument('--out',type=Path,default=ROOT/'results/gn1_comparison_20261118');p.add_argument('--index',type=int)
    args=p.parse_args()
    if args.command=='run':run(args.out.resolve())
    else:
        try:worker(args.out.resolve(),args.index)
        except Exception:traceback.print_exc();raise

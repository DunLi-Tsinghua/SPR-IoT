"""Generic, manifest-driven third-round real-Broker probes; no task synthesis.

Manifest: {tasks:[{task:{id,policy,filters,required,forbidden,principal},
policies:{method:policy-or-{result_file:path}}, challenges:[{topic,label}],
repeats:1}]}. label is required/forbidden/unspecified; no requirements inferred.
"""
import argparse,csv,hashlib,json,socket,subprocess,sys,time,traceback
from pathlib import Path
import broker_round2 as wire
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from src.independent import accepts

def decision(policy,kind,value):
    for r in sorted((r for r in policy if r['kind']==kind),key=lambda r:-r['priority']):
        matched=r['topic']==value if kind.endswith('Literal') else accepts(r['topic'],value)
        if matched:
            return bool(r['allow'])
    return False

def expected(policy,f,t):
    subscribed=decision(policy,'subscribeLiteral',f) or decision(policy,'subscribePattern',f)
    return subscribed,subscribed and accepts(f,t) and decision(policy,'publishClientReceive',t)

def validate(policy):
    allowed={'subscribeLiteral','subscribePattern','publishClientReceive'}
    if any(r['kind'] not in allowed for r in policy):raise ValueError('Unsupported event')
    kinds={r['kind'] for r in policy if r['kind'].startswith('subscribe')}
    if len(kinds)>1:raise ValueError('Mixed subscription ACL types not modeled')
    for kind in allowed:
        ps=[r['priority'] for r in policy if r['kind']==kind]
        if len(set(ps))!=len(ps):raise ValueError('Tied priority unsupported')

def load_policy(x):
    if isinstance(x,dict) and 'result_file' in x:
        p=(ROOT/x['result_file']).resolve()
        if not p.is_relative_to(ROOT):raise ValueError('Result input must stay inside project')
        d=json.loads(p.read_text(encoding='utf-8'))
        return d['policy'],str(p),hashlib.sha256(p.read_bytes()).hexdigest()
    return x,None,None

def probe(port,f,t,mid,window):
    reader=publisher=None
    try:
        reader=wire.MQTT(port,'reader');suback=reader.subscribe(f)
        publisher=wire.MQTT(port,'publisher');publisher.publish(t,mid)
        messages=[];reader.s.settimeout(min(.2,window));until=time.monotonic()+window
        while time.monotonic()<until:
            try:
                h,p=reader.packet()
                if h>>4==3:
                    n=int.from_bytes(p[:2],'big');i=2+n;qos=(h>>1)&3
                    if qos:reader.send(0x40,p[i:i+2]);i+=2
                    messages.append(dict(topic=p[2:2+n].decode(),payload=p[i:].decode(),dup=bool(h&8),qos=qos))
            except socket.timeout:pass
        return dict(suback=suback,puback_verified=True,delivered=sum(m['payload']==mid for m in messages),messages=messages)
    finally:
        for c in [reader,publisher]:
            if c is not None:c.close()

def main(a):
    out=a.out.resolve()
    if not out.is_relative_to(ROOT):raise ValueError('Output must stay inside project')
    if out.exists() and any(out.iterdir()):raise FileExistsError('Use a clean --out; previous evidence is preserved')
    out.mkdir(parents=True,exist_ok=True)
    source=a.manifest.resolve()
    if not source.is_relative_to(ROOT):raise ValueError('Manifest must stay inside project')
    manifest=json.loads(source.read_text(encoding='utf-8'))
    (out/'input_manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    broker=a.broker.resolve();plugin=a.plugin.resolve();ctrl=broker.with_name('mosquitto_ctrl.exe')
    metadata=dict(manifest_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),broker_sha256=hashlib.sha256(broker.read_bytes()).hexdigest(),plugin_sha256=hashlib.sha256(plugin.read_bytes()).hexdigest(),version=subprocess.run([str(broker),'-h'],capture_output=True,text=True).stdout,host='127.0.0.1',port=a.port,qos=1,receive_window_seconds=a.window)
    (out/'environment.json').write_text(json.dumps(metadata,indent=2),encoding='utf-8')
    with socket.socket() as test:test.bind(('127.0.0.1',a.port))
    for name in ['reader','publisher']:
        target=out/f'identity_{name}.json'
        r=subprocess.run([str(ctrl),'dynsec','init',str(target),name,wire.PASSWORD],capture_output=True,text=True)
        (out/f'identity_{name}.log').write_text(r.stdout+r.stderr,encoding='utf-8');r.check_returncode()
        wire.IDENTITIES[name]=json.loads(target.read_text())['clients'][0]
    rows=[];skips=[];mismatches=[]
    for entry in manifest['tasks']:
        task=entry['task'];id=task['id']
        if any(c not in 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_-' for c in id):raise ValueError('Unsafe task id')
        principal=task.get('principal',dict(username='reader',clientid='reader'))
        if principal!={'username':'reader','clientid':'reader'}:raise ValueError('Only declared fixed reader identity currently supported')
        catalog=[dict(topic=t,label='required') for t in task['required']]+[dict(topic=t,label='forbidden') for t in task['forbidden']]
        topics=[dict(x,domain='catalog') for x in catalog]+[dict(x,domain='challenge') for x in entry.get('challenges',[])]
        if any(x['label'] not in ['required','forbidden','unspecified'] for x in topics):raise ValueError('Unsupported requirement label')
        for method,reference in entry['policies'].items():
            if any(c not in 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_-' for c in method):raise ValueError('Unsafe method id')
            policy,result_file,result_hash=load_policy(reference)
            if policy is None:
                skips.append(dict(task=id,method=method,status='no_policy',result_file=result_file));continue
            validate(policy);case=out/f'{id}_{method}';case.mkdir()
            (case/'input.json').write_text(json.dumps(dict(task=task,policy=policy,challenges=entry.get('challenges',[]),result_file=result_file,result_sha256=result_hash),indent=2))
            security=case/'dynamic-security.json';cfg=wire.config(policy)
            # A matching publisher grant is explicit for every tested $ hierarchy.
            for i,prefix in enumerate(sorted({x['topic'].split('/')[0] for x in topics if x['topic'].startswith('$')})):
                cfg['roles'][1]['acls'].append(dict(acltype='publishClientSend',topic=prefix+'/#',allow=True,priority=i+2))
            security.write_text(json.dumps(cfg,indent=2))
            conf=case/'mosquitto.conf';conf.write_text(f'listener {a.port} 127.0.0.1\nallow_anonymous false\npersistence false\nplugin {plugin.as_posix()}\nplugin_opt_config_file {security.as_posix()}\nlog_type all\nconnection_messages true\n')
            with (case/'broker.log').open('w') as log:
                proc=subprocess.Popen([str(broker),'-c',str(conf),'-v'],stdout=log,stderr=log)
                try:
                    deadline=time.monotonic()+8
                    while True:
                        try:
                            with socket.create_connection(('127.0.0.1',a.port),.2):break
                        except OSError:
                            if proc.poll() is not None or time.monotonic()>deadline:raise RuntimeError('Broker startup failed')
                            time.sleep(.1)
                    for repeat in range(entry.get('repeats',1)):
                        for f in task['filters']:
                            for x in topics:
                                mid=f'{id}:{method}:{repeat}:{len(rows)}';obs=probe(a.port,f,x['topic'],mid,a.window)
                                sub,delivery=expected(policy,f,x['topic'])
                                row=dict(task=id,method=method,repeat=repeat,filter=f,topic=x['topic'],domain=x['domain'],label=x['label'],message_id=mid,expected_subscribe=sub,expected_delivery=delivery,**{k:v for k,v in obs.items() if k!='messages'})
                                rows.append(row)
                                if (obs['suback']!=128)!=sub or bool(obs['delivered'])!=delivery:mismatches.append(row)
                                with (case/'client.jsonl').open('a') as fhandle:fhandle.write(json.dumps(dict(**row,messages=obs['messages']))+'\n')
                finally:proc.terminate();proc.wait(timeout=5)
    with (out/'probes.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=rows[0].keys());w.writeheader();w.writerows(rows)
    summaries=[]
    for id,method,domain,label in sorted({(r['task'],r['method'],r['domain'],r['label']) for r in rows}):
        group=[r for r in rows if (r['task'],r['method'],r['domain'],r['label'])==(id,method,domain,label)]
        topics=sorted({r['topic'] for r in group});obtained=sum(any(r['topic']==t and r['delivered'] for r in group) for t in topics)
        summaries.append(dict(task=id,method=method,domain=domain,label=label,unique_topics=len(topics),obtained_topics=obtained,probe_rows=len(group)))
    with (out/'summary.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=summaries[0].keys());w.writeheader();w.writerows(summaries)
    status=dict(status='executed',probe_rows=len(rows),skips=skips,mismatches=mismatches,scope='Finite fresh-connection observations and independent concrete checks; no universal denial proof')
    (out/'status.json').write_text(json.dumps(status,indent=2));print(json.dumps(status));return bool(mismatches)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--manifest',type=Path,required=True);p.add_argument('--out',type=Path,default=ROOT/'results/round3/broker');p.add_argument('--broker',type=Path,default=ROOT/'tools/broker/2.1.2/mosquitto.exe');p.add_argument('--plugin',type=Path,default=ROOT/'tools/broker/2.1.2/mosquitto_dynamic_security.dll');p.add_argument('--port',type=int,default=28886);p.add_argument('--window',type=float,default=.6)
    raise SystemExit(main(p.parse_args()))

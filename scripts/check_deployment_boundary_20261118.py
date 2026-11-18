"""Small, separate deployment-contract regression on two frozen repaired snapshots.

No solver run, no modification of historical inputs, and no performance benchmark.
Shared requests are observations outside the proven plain-subscription interface.
"""
import argparse, copy, hashlib, json, socket, subprocess, sys, time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'scripts'))
import broker_round2 as wire
from broker_round3 import probe
from src.deployment_contract import verify_literal_snapshot


def main(out):
    out=out.resolve()
    if not out.is_relative_to(ROOT) or out.exists():
        raise ValueError('Use a new output directory inside SPR project')
    out.mkdir(parents=True)
    binary=ROOT/'tools/broker/2.1.2/mosquitto.exe'
    plugin=binary.with_name('mosquitto_dynamic_security.dll')
    for name in ['reader','publisher']:
        p=out/f'identity_{name}.json'
        run=subprocess.run([str(binary.with_name('mosquitto_ctrl.exe')),'dynsec','init',str(p),name,wire.PASSWORD],capture_output=True,text=True,timeout=15)
        (out/f'identity_{name}.log').write_text(run.stdout+run.stderr);run.check_returncode()
        wire.IDENTITIES[name]=json.loads(p.read_text())['clients'][0]
    manifest_path=ROOT/'results/round4/broker/manifest.json'
    resolved_path=ROOT/'results/round4/broker/resolved_policies.json'
    manifest=json.loads(manifest_path.read_text());resolved=json.loads(resolved_path.read_text())
    entries=manifest['tasks'][:2]
    plan=dict(tasks=[e['task']['id'] for e in entries],method='SPR_open',repeats=2,
              filters=['approved plain','unapproved plain descendant','shared approved underlying filter','shared unapproved underlying filter'],
              topics=['first existing required topic','first existing forbidden topic'],window_seconds=.8,
              scope='finite regression; shared requests descriptive, not a new supported language')
    (out/'plan.json').write_text(json.dumps(plan,indent=2))
    sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    (out/'sources.json').write_text(json.dumps({str(p.relative_to(ROOT)):sha(p) for p in [manifest_path,resolved_path,binary,plugin]},indent=2))
    rows=[];identities=[];controls=[];contracts=[]
    port=28902
    with socket.socket() as check:check.bind(('127.0.0.1',port))
    for entry in entries:
        task=entry['task'];policy=resolved[task['id']]['SPR_open']['policy']
        cfg=wire.config(policy);contract=verify_literal_snapshot(cfg,policy,task)
        contracts.append(dict(task=task['id'],**contract))
        case=out/task['id'];case.mkdir()
        security=case/'dynamic-security.json';security.write_text(json.dumps(cfg,indent=2))
        conf=case/'mosquitto.conf';conf.write_text(f'listener {port} 127.0.0.1\nallow_anonymous false\npersistence false\nplugin {plugin.as_posix()}\nplugin_opt_config_file {security.as_posix()}\nlog_type all\nconnection_messages true\n')
        with (case/'broker.log').open('w') as log:
            proc=subprocess.Popen([str(binary),'-c',str(conf),'-v'],stdout=log,stderr=log,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
            try:
                deadline=time.monotonic()+8
                while True:
                    try:c=wire.MQTT(port,'reader');c.close();break
                    except (OSError,EOFError,RuntimeError):
                        if proc.poll() is not None or time.monotonic()>deadline:raise RuntimeError('Broker readiness failed')
                        time.sleep(.05)
                f=task['filters'][0];prefix=f[:-1];outside=prefix+'public/#'
                requests=[('approved',f),('unapproved',outside),('shared_approved','$share/sprreview/'+f),('shared_unapproved','$share/sprreview/'+outside)]
                required=next(q['topic'] for q in entry['requests'] if q['label']=='required')
                forbidden=next(q['topic'] for q in entry['requests'] if q['label']=='forbidden')
                for position in ['before','after']:
                    if position=='after':break
                    obs=probe(port,f,required,f'{task["id"]}:control:{position}',.5)
                    controls.append(dict(task=task['id'],position=position,**obs))
                for repeat in range(2):
                    for label,requested in requests:
                        for kind,topic in [('required',required),('forbidden',forbidden)]:
                            mid=f'{task["id"]}:{repeat}:{label}:{kind}'
                            obs=probe(port,requested,topic,mid,.8)
                            row=dict(task=task['id'],repeat=repeat,request_class=label,filter=requested,topic_kind=kind,topic=topic,message_id=mid,**obs)
                            rows.append(row)
                            with (case/'client.jsonl').open('a') as stream:stream.write(json.dumps(row)+'\n')
                controls.append(dict(task=task['id'],position='after',**probe(port,f,required,f'{task["id"]}:control:after',.5)))
                for label,user,password,clientid in [('wrong_password','reader','incorrect','reader'),('wrong_username','intruder',wire.PASSWORD,'intruder'),('wrong_clientid','reader',wire.PASSWORD,'other')]:
                    client=object.__new__(wire.MQTT);client.s=socket.create_connection(('127.0.0.1',port),2);client.s.settimeout(2)
                    try:
                        client.send(0x10,wire.utf('MQTT')+bytes([4,194])+bytes([0,30])+wire.utf(clientid)+wire.utf(user)+wire.utf(password))
                        header,body=client.packet()
                        identities.append(dict(task=task['id'],test=label,header=header,connack_hex=body.hex(),denied=header==0x20 and len(body)==2 and body[1]!=0))
                    finally:client.s.close()
            finally:
                proc.terminate()
                try:proc.wait(timeout=5)
                except subprocess.TimeoutExpired:proc.kill();proc.wait(timeout=2)
        (case/'loaded-security.json').write_bytes(security.read_bytes())
    plain=[r for r in rows if not r['request_class'].startswith('shared')]
    assert all(r['suback']==128 and r['delivered']==0 for r in plain if r['request_class']=='unapproved')
    assert all(r['suback']!=128 and bool(r['delivered'])==(r['topic_kind']=='required') for r in plain if r['request_class']=='approved')
    assert all(r['delivered']==1 for r in controls) and all(r['denied'] for r in identities)
    summary=dict(status='passed',new_probe_records=len(rows),positive_controls=len(controls),identity_denials=sum(r['denied'] for r in identities),
                 plain_probe_records=len(plain),shared_probe_records=len(rows)-len(plain),
                 shared_suback_values=sorted({r['suback'] for r in rows if r['request_class'].startswith('shared')}),
                 shared_forbidden_deliveries=sum(r['delivered'] for r in rows if r['request_class'].startswith('shared') and r['topic_kind']=='forbidden'),
                 historical_probes=127,historical_controls=80,not_pooled_with_historical=True,
                 scope='Two existing repaired snapshots, fresh loopback connections, finite negative regression; no arbitrary-client proof')
    (out/'results.json').write_text(json.dumps(dict(summary=summary,contracts=contracts,probes=rows,controls=controls,identity_checks=identities),indent=2))
    print(json.dumps(summary,indent=2))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--out',type=Path,default=ROOT/'results/deployment_boundary_20261118')
    main(parser.parse_args().out)

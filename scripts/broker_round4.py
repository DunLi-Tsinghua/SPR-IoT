"""Fourth-round actual Mosquitto E5/E6. Frozen manifest; no solver invocation."""
import argparse,csv,hashlib,json,math,os,platform,statistics,subprocess,sys,threading,time,traceback
from pathlib import Path
import broker_round2 as wire
from broker_round3 import expected,validate
ROOT=Path(__file__).resolve().parents[1]

def csvwrite(path,rows):
 if not rows:return
 keys=list(dict.fromkeys(k for r in rows for k in r))
 with path.open('w',newline='',encoding='utf-8') as f:
  w=csv.DictWriter(f,fieldnames=keys);w.writeheader();w.writerows(rows)

def dump(path,x):path.write_text(json.dumps(x,indent=2),encoding='utf-8')
def hashfile(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def connect(user):
 c=wire.MQTT(PORT,user);c.s.setsockopt(__import__('socket').IPPROTO_TCP,__import__('socket').TCP_NODELAY,1);return c

def read_publish(c):
 h,b=c.packet()
 if h>>4!=3:raise ValueError(('unexpected_reader_packet',h))
 n=int.from_bytes(b[:2],'big');i=2+n;qos=(h>>1)&3
 if qos:c.send(0x40,b[i:i+2]);i+=2
 return dict(topic=b[2:2+n].decode(),payload=b[i:].decode(),dup=bool(h&8),qos=qos)

def once(user,f,t,mid,window):
 reader=publisher=None
 try:
  reader=connect(user);sub=reader.subscribe(f);publisher=connect('publisher');publisher.publish(t,mid)
  messages=[];reader.s.settimeout(.1);until=time.monotonic()+window
  while time.monotonic()<until:
   try:messages.append(read_publish(reader))
   except TimeoutError:pass
  return dict(status='observed',connack_verified=True,suback=sub,puback_verified=True,delivered=sum(m['payload']==mid for m in messages),messages=messages)
 except Exception as ex:return dict(status='probe_error',connack_verified=None,suback=None,puback_verified=None,delivered=None,messages=[],error=repr(ex))
 finally:
  for c in [reader,publisher]:
   if c is not None:
    try:c.close()
    except OSError:pass

def exported(policy,requests):
 validate(policy)
 if len({(r['kind'],r['topic']) for r in policy})!=len(policy):raise ValueError('Duplicate deployed ACL key')
 if any(x in r['topic'].split('/') for r in policy for x in ['%u','%c']):raise ValueError('Unmodeled identity substitution')
 cfg=wire.config(policy)
 cfg['clients'].append(wire.auth('observer','observer'))
 cfg['roles'].append(dict(rolename='observer',acls=[dict(acltype=k,topic='spr4_control/positive',allow=True,priority=1) for k in ['subscribeLiteral','publishClientReceive']]))
 for i,prefix in enumerate(sorted({q['topic'].split('/')[0] for q in requests if q['topic'].startswith('$')})):
  cfg['roles'][1]['acls'].append(dict(acltype='publishClientSend',topic=prefix+'/#',allow=True,priority=i+2))
 return cfg

class Deployment:
 def __init__(self,entry,method,record,case):
  self.entry=entry;self.policy=record['policy'];self.case=case;self.case.mkdir(parents=True);self.proc=None;self.log=None;self.controls=[]
  self.metrics=dict(task=entry['task']['id'],method=method,algorithm_status=record['algorithm_status'],reader_rules_before=len(entry['task']['policy']),reader_rules=len(self.policy) if self.policy is not None else None,configuration_bytes=None,generation_seconds=None,load_seconds=None,status='NA',reason='')
  dump(case/'input.json',dict(task=entry['task'],requests=entry['requests'],policy=self.policy,source=record))
 def start(self):
  if self.policy is None:self.metrics.update(reason='algorithm_'+self.metrics['algorithm_status']);return False
  t=time.perf_counter();cfg=exported(self.policy,self.entry['requests']);security=self.case/'dynamic-security.json';encoded=json.dumps(cfg,separators=(',',':')).encode();security.write_bytes(encoded)
  conf=self.case/'mosquitto.conf';conf.write_text(f'listener {PORT} 127.0.0.1\nallow_anonymous false\npersistence false\nplugin {PLUGIN.as_posix()}\nplugin_opt_config_file {security.as_posix()}\nlog_type all\nconnection_messages true\n')
  self.metrics.update(generation_seconds=time.perf_counter()-t,configuration_bytes=len(encoded),broker_configuration_bytes=conf.stat().st_size,total_configuration_acls=sum(len(x['acls']) for x in cfg['roles']))
  self.log=(self.case/'broker.log').open('w');t=time.perf_counter();self.proc=subprocess.Popen([str(BROKER),'-c',str(conf),'-v'],stdout=self.log,stderr=self.log,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0));deadline=time.monotonic()+8
  while True:
   try:c=connect('observer');self.metrics['load_seconds']=time.perf_counter()-t;c.close();break
   except (OSError,EOFError,RuntimeError):
    if self.proc.poll() is not None or time.monotonic()>deadline:raise RuntimeError('Broker startup/authenticated readiness failed')
    time.sleep(.02)
  self.metrics['status']='executed';self.control('start');return True
 def control(self,position):
  r=once('observer','spr4_control/positive','spr4_control/positive',self.case.name+':control:'+position,.2);self.controls.append(dict(position=position,**r));dump(self.case/'positive_controls.json',self.controls)
 def stop(self):
  if self.proc is not None:
   self.proc.terminate()
   try:self.proc.wait(timeout=5)
   except subprocess.TimeoutExpired:self.proc.kill();self.proc.wait(timeout=2)
  if self.log is not None:self.log.close()
  if self.controls and any(r['status']!='observed' or not r['delivered'] or r['suback']==128 for r in self.controls):self.metrics.update(status='control_failure',reason='positive control failed')
  dump(self.case/'deployment.json',self.metrics)

def prepare(a):
 global BROKER,PLUGIN,PORT
 BROKER=(ROOT/'tools/broker/2.1.2/mosquitto.exe').resolve();PLUGIN=BROKER.with_name('mosquitto_dynamic_security.dll')
 out=a.out.resolve()
 if not out.is_relative_to(ROOT):raise ValueError('Output outside project')
 manifest=json.loads(a.manifest.read_text());out.mkdir(parents=True,exist_ok=True)
 frozen=out/'manifest.json'
 if frozen.exists():
  if json.loads(frozen.read_text())!=manifest:raise ValueError('Frozen input changed')
 else:dump(frozen,manifest)
 resolved=out/'resolved_policies.json'
 if not resolved.exists():
  records={}
  for entry in manifest['tasks']:
   records[entry['task']['id']]={}
   for method,ref in entry['policies'].items():
    if 'inline' in ref:r=dict(policy=ref['inline'],algorithm_status='original',source='frozen manifest')
    else:
     path=(ROOT/ref['result_file']).resolve()
     if not path.is_relative_to(ROOT):raise ValueError('Result outside project')
     if not path.exists():raise FileNotFoundError('Wait for prescheduled offline result: '+str(path))
     d=json.loads(path.read_text());r=dict(policy=d.get('policy'),algorithm_status=d['result']['status'],source=ref['result_file'],sha256=hashfile(path),algorithm_audit=d.get('audit'))
    records[entry['task']['id']][method]=r
  dump(resolved,records)
 records=json.loads(resolved.read_text())
 for name in ['reader','publisher','observer']:
  target=out/f'identity_{name}.json'
  if not target.exists():
   start=time.perf_counter();r=subprocess.run([str(BROKER.with_name('mosquitto_ctrl.exe')),'dynsec','init',str(target),name,wire.PASSWORD],capture_output=True,text=True,timeout=15);(out/f'identity_{name}.log').write_text(r.stdout+r.stderr);r.check_returncode()
  wire.IDENTITIES[name]=json.loads(target.read_text())['clients'][0]
 PORT=manifest['ports'][a.phase]
 with __import__('socket').socket() as check:check.bind(('127.0.0.1',PORT))
 if not (out/'environment.json').exists():dump(out/'environment.json',dict(python=sys.version,platform=platform.platform(),logical_cpu=os.cpu_count(),broker_sha256=hashfile(BROKER),plugin_sha256=hashfile(PLUGIN),version=subprocess.run([str(BROKER),'-h'],capture_output=True,text=True).stdout,manifest_sha256=hashfile(a.manifest),host='127.0.0.1',ports=manifest['ports'],testbed='single machine, not isolated from other user/system load',tcp_nodelay=True))
 return out,manifest,records

def base_na(entry,method,record,reason,**extra):
 return dict(task=entry['task']['id'],method=method,algorithm_status=record['algorithm_status'],status='NA',reason=reason,reader_rules_before=len(entry['task']['policy']),reader_rules=len(record['policy']) if record['policy'] is not None else None,configuration_bytes=None,generation_seconds=None,load_seconds=None,**extra)

def e5(out,m,records):
 phase=out/'E5'
 if phase.exists():raise FileExistsError('E5 evidence already exists')
 phase.mkdir();start=time.monotonic();deadline=start+m['phase_e5_budget_s'];probes=[];deployments=[];mismatches=[]
 for entry in m['tasks']:
  id=entry['task']['id']
  for method in entry['policies']:
   rec=records[id][method]
   if time.monotonic()>deadline:deployments.append(base_na(entry,method,rec,'budget_exhausted',phase='E5'));continue
   d=Deployment(entry,method,rec,phase/f'{id}_{method}')
   try:
    if d.start():
     for f in entry['task']['filters']:
      for q in entry['requests']:
       if time.monotonic()>deadline:d.metrics.update(status='partial',reason='budget_exhausted');break
       mid=f'E5:{id}:{method}:{len(probes)}';obs=once('reader',f,q['topic'],mid,.6);sub,delivery=expected(d.policy,f,q['topic'])
       row=dict(task=id,method=method,filter=f,topic=q['topic'],domain=q['domain'],label=q['label'],message_id=mid,expected_subscribe=sub,expected_delivery=delivery,**{k:v for k,v in obs.items() if k!='messages'})
       probes.append(row)
       if obs['status']=='observed' and ((obs['suback']!=128)!=sub or bool(obs['delivered'])!=delivery):mismatches.append(row)
       if obs['status']!='observed':d.metrics.update(status='probe_failure',reason=obs.get('error','probe failed'))
       with (d.case/'client.jsonl').open('a') as fhandle:fhandle.write(json.dumps(dict(**row,messages=obs['messages']))+'\n')
     d.control('end')
   except Exception as ex:d.metrics.update(status='deployment_error',reason=repr(ex));(d.case/'failure.log').write_text(traceback.format_exc())
   finally:d.stop()
   deployments.append(dict(d.metrics,phase='E5'));csvwrite(phase/'deployments.csv',deployments);csvwrite(phase/'probes.csv',probes)
 summary=[]
 for entry in m['tasks']:
  id=entry['task']['id']
  for method in entry['policies']:
   dep=next(x for x in deployments if x['task']==id and x['method']==method)
   for domain,label in sorted({(q['domain'],q['label']) for q in entry['requests']}):
    topics={q['topic'] for q in entry['requests'] if q['domain']==domain and q['label']==label};g=[r for r in probes if r['task']==id and r['method']==method and r['domain']==domain and r['label']==label]
    known=sum(any(r['topic']==t and r['delivered'] for r in g) for t in topics)
    good=dep['status']=='executed' and all(r['status']=='observed' for r in g) and len(g)==len(topics)*len(entry['task']['filters'])
    summary.append(dict(task=id,method=method,domain=domain,label=label,status=dep['status'] if good else 'NA',reason=dep.get('reason',''),topic_denominator=len(topics),topic_obtained=known if good else None,observed_obtained_topics=known if g else None,probe_rows=len(g),algorithm_status=dep['algorithm_status']))
 csvwrite(out/'deployments.csv',deployments);csvwrite(out/'probes.csv',probes);csvwrite(out/'delivery_summary.csv',summary)
 status=dict(phase='E5',status='executed',wall_seconds=time.monotonic()-start,deployments=len(deployments),main_probes=len(probes),mismatches=mismatches,counts={s:sum(d['status']==s for d in deployments) for s in sorted({d['status'] for d in deployments})})
 dump(out/'status_E5.json',status);print(json.dumps(status));return bool(mismatches)

def p95(xs):
 a=sorted(xs);p=.95*(len(a)-1);i=int(p);return a[i]+(a[min(i+1,len(a)-1)]-a[i])*(p-i)

def workload(d,repeat,order,deadline):
 t=d.entry['task'];receiver=publisher=None;thread=None;stop=threading.Event();events={};sent={};arrivals={};received=[];errors=[];rows=[]
 result=dict(authentication_reader_ms=None,authentication_publisher_ms=None,subscription_total_ms=None,latency_median_ms=None,latency_p95_ms=None,latency_mean_ms=None,delivered_messages=0,planned_messages=10,workload_seconds=None,workload_status='not_started')
 try:
  begin=time.perf_counter();receiver=connect('reader');result['authentication_reader_ms']=(time.perf_counter()-begin)*1000
  begin=time.perf_counter();publisher=connect('publisher');result['authentication_publisher_ms']=(time.perf_counter()-begin)*1000;subs=[]
  for f in t['filters']:
   begin=time.perf_counter();ack=receiver.subscribe(f);subs.append(dict(filter=f,suback=ack,authorization_ms=(time.perf_counter()-begin)*1000))
  result['subscription_total_ms']=sum(x['authorization_ms'] for x in subs);dump(d.case/'subscription.json',subs)
  topic=t['required'][0];result['workload_topic']=topic
  allowed=any(expected(d.policy,f,topic)[1] for f in t['filters'])
  if not allowed:result['workload_status']='no_authorized_business_path';return result,rows
  receiver.s.settimeout(.05)
  def receive():
   while not stop.is_set():
    try:
     message=read_publish(receiver);now=time.perf_counter_ns();received.append(dict(received_ns=now,**message));payload=message['payload']
     if payload in events:
      arrivals.setdefault(payload,now);events[payload].set()
    except TimeoutError:pass
    except Exception as ex:
     if not stop.is_set():errors.append(repr(ex))
     break
  thread=threading.Thread(target=receive,daemon=True);thread.start();work_start=time.perf_counter()
  for i in range(10):
   if time.monotonic()>deadline:result['workload_status']='budget_exhausted';break
   prefix=f'spr4:{hashlib.sha256(d.case.name.encode()).hexdigest()[:8]}:{repeat}:{i:02d}';payload=prefix.ljust(64,'x');event=threading.Event();events[payload]=event;sent[payload]=time.perf_counter_ns();begin=time.perf_counter();publisher.publish(topic,payload);puback_ms=(time.perf_counter()-begin)*1000;arrived=event.wait(1)
   rows.append(dict(task=t['id'],method=d.metrics['method'],repeat=repeat,order=order,message_index=i,message_id=payload,topic=topic,payload_bytes=len(payload.encode()),qos=1,puback_verified=True,send_ns=sent[payload],receive_ns=arrivals.get(payload),latency_ms=(arrivals[payload]-sent[payload])/1e6 if arrived else None,puback_ms=puback_ms,status='received' if arrived else 'not_observed',requirement_state='conflict' if topic in t['forbidden'] else 'required'))
   time.sleep(.01)
  result['workload_seconds']=time.perf_counter()-work_start;lat=[r['latency_ms'] for r in rows if r['status']=='received'];result['delivered_messages']=len(lat)
  complete=len(lat)==10 and len(rows)==10 and not errors
  result['workload_status']='complete' if complete else result['workload_status'] if result['workload_status']=='budget_exhausted' else 'partial_delivery'
  if complete:result.update(latency_median_ms=statistics.median(lat),latency_p95_ms=p95(lat),latency_mean_ms=statistics.mean(lat))
  return result,rows
 except Exception as ex:result.update(workload_status='workload_error',workload_error=repr(ex));return result,rows
 finally:
  stop.set()
  if thread:thread.join(timeout=1)
  for c in [receiver,publisher]:
   if c is not None:
    try:c.close()
    except OSError:pass
  dump(d.case/'received_workload.json',dict(messages=received,thread_errors=errors))

def e6(out,m,records):
 phase=out/'E6'
 if phase.exists():raise FileExistsError('E6 evidence already exists')
 phase.mkdir();dump(out/'order.json',m['e6_order']);start=time.monotonic();used=json.loads((out/'status_E5.json').read_text())['wall_seconds'];deadline=start+max(0,m['total_budget_s']-used);entries={e['task']['id']:e for e in m['tasks']};runs=[];messages=[]
 for pair in m['e6_order']:
  entry=entries[pair['task']];id=entry['task']['id']
  for order,method in enumerate(pair['methods']):
   rec=records[id][method];extra=dict(phase='E6',repeat=pair['repeat'],order=order,seed=m['seed'])
   if time.monotonic()>deadline:runs.append(base_na(entry,method,rec,'budget_exhausted',**extra));continue
   d=Deployment(entry,method,rec,phase/f'{id}_r{pair["repeat"]}_o{order}_{method}')
   try:
    if d.start():
     result,raw=workload(d,pair['repeat'],order,deadline);d.metrics.update(result);messages.extend(raw);d.control('end')
   except Exception as ex:d.metrics.update(status='deployment_error',reason=repr(ex));(d.case/'failure.log').write_text(traceback.format_exc())
   finally:d.stop()
   runs.append(dict(d.metrics,**extra));csvwrite(out/'overhead_runs.csv',runs);csvwrite(out/'message_latency.csv',messages)
 previous=list(csv.DictReader((out/'deployments.csv').open())) if (out/'deployments.csv').exists() else [];csvwrite(out/'deployments.csv',previous+runs)
 metrics=['reader_rules','configuration_bytes','generation_seconds','load_seconds','authentication_reader_ms','authentication_publisher_ms','subscription_total_ms','latency_median_ms','latency_p95_ms'];paired=[]
 for pair in m['e6_order']:
  group=[r for r in runs if r['task']==pair['task'] and r['repeat']==pair['repeat']];a=next(r for r in group if r['method']=='B0');b=next(r for r in group if r['method']=='SPR_open');complete=a['status']==b['status']=='executed' and a.get('workload_status')==b.get('workload_status')=='complete'
  row=dict(task=pair['task'],repeat=pair['repeat'],method_order='|'.join(pair['methods']),status='complete_pair' if complete else 'NA',before_status=a['status'],after_status=b['status'],before_algorithm_status=a['algorithm_status'],after_algorithm_status=b['algorithm_status'],complete_business_pair=complete,efficiency_superiority_claim=False)
  for metric in metrics:
   av=a.get(metric);bv=b.get(metric);row['before_'+metric]=av;row['after_'+metric]=bv;row['delta_'+metric]=(bv-av) if complete and av is not None and bv is not None else None
  paired.append(row)
 csvwrite(out/'paired_differences.csv',paired)
 status=dict(phase='E6',status='executed',wall_seconds=time.monotonic()-start,deployment_slots=len(runs),workload_message_rows=len(messages),complete_pairs=sum(r['status']=='complete_pair' for r in paired),planned_pairs=len(paired),counts={s:sum(r['status']==s for r in runs) for s in sorted({r['status'] for r in runs})},scope='10 messages summarize each run; 5 paired runs per task, not message-based confidence intervals')
 dump(out/'status_E6.json',status);print(json.dumps(status));return 0

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--phase',choices=['E5','E6'],required=True);p.add_argument('--manifest',type=Path,default=ROOT/'data/manifests/round4_broker.json');p.add_argument('--out',type=Path,default=ROOT/'results/round4/broker');a=p.parse_args();out,m,records=prepare(a);raise SystemExit(e5(out,m,records) if a.phase=='E5' else e6(out,m,records))

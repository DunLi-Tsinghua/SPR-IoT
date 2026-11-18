"""Actual Mosquitto Dynamic Security test. No broker simulator or pip dependency.

Requires Mosquitto 2.1.2 distribution with dynamic-security plugin.
Only loopback is used. Reads existing repair outputs; never starts another project.
"""
import argparse, base64, hashlib, json, socket, struct, subprocess, time, csv
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'results/raw/round2/broker_spr2'
PASSWORD = 'spr-local-test-only'

def utf(s):
    b=s.encode(); return struct.pack('!H',len(b))+b

class MQTT:
    def __init__(self, port, user, password=PASSWORD, clientid=None):
        self.s=socket.create_connection(('127.0.0.1',port),2); self.s.settimeout(2)
        self.send(0x10,utf('MQTT')+bytes([4,194])+struct.pack('!H',30)+utf(clientid or user)+utf(user)+utf(password))
        h,b=self.packet()
        if h!=0x20 or b!=b'\x00\x00': raise RuntimeError(('CONNACK',h,b.hex()))
    def send(self,h,b):
        n=len(b); v=[]
        while True:
            x=n%128;n//=128;v.append(x|(128 if n else 0))
            if not n:break
        self.s.sendall(bytes([h,*v])+b)
    def exact(self,n):
        b=b''
        while len(b)<n:
            p=self.s.recv(n-len(b))
            if not p:raise EOFError()
            b+=p
        return b
    def packet(self):
        h=self.exact(1)[0];n=0;m=1
        while True:
            x=self.exact(1)[0];n+=(x&127)*m;m*=128
            if not x&128:break
        return h,self.exact(n)
    def subscribe(self,f):
        self.send(0x82,b'\x00\x01'+utf(f)+b'\x01')
        h,b=self.packet()
        if h!=0x90:raise RuntimeError(('SUBACK',h,b.hex()))
        return b[-1]
    def publish(self,t,p):
        self.send(0x32,utf(t)+b'\x00\x02'+p.encode())
        h,b=self.packet()
        if h!=0x40:raise RuntimeError(('PUBACK',h,b.hex()))
    def close(self):
        try:self.send(0xe0,b'')
        finally:self.s.close()

IDENTITIES={}
def auth(name,role):
    return dict(IDENTITIES[name],clientid=name,roles=[dict(rolename=role,priority=1)])

def config(policy):
    acl=lambda r:dict(acltype=r['kind'],topic=r['topic'],allow=r['allow'],priority=r['priority'])
    return dict(defaultACLAccess={k:False for k in ['publishClientSend','publishClientReceive','subscribe','unsubscribe']},clients=[auth('reader','reader'),auth('publisher','publisher')],groups=[],roles=[dict(rolename='reader',acls=[acl(r) for r in policy]),dict(rolename='publisher',acls=[dict(acltype='publishClientSend',topic='#',allow=True,priority=1)])])

def run(args):
    global OUT
    OUT=Path(args.out).resolve() if args.out else OUT
    OUT.mkdir(parents=True,exist_ok=True)
    if not args.broker or not args.plugin:
        status=dict(status='blocked',broker_runs=0,reason='Official Mosquitto executable and Dynamic Security plugin not available. Pass --broker and --plugin.',date='2026-10-28')
        (OUT/'status.json').write_text(json.dumps(status,indent=2)); print(json.dumps(status));return 2
    broker=Path(args.broker).resolve();plugin=Path(args.plugin).resolve()
    ctrl=broker.with_name('mosquitto_ctrl.exe')
    for name in ['reader','publisher']:
        target=OUT/f'identity_{name}.json'
        if not target.exists():
            r=subprocess.run([str(ctrl),'dynsec','init',str(target),name,PASSWORD],capture_output=True,text=True)
            (OUT/f'identity_{name}.log').write_text(r.stdout+r.stderr)
            r.check_returncode()
        IDENTITIES[name]=json.loads(target.read_text())['clients'][0]
    # Refuse an occupied port; never connect the pilot clients to an existing broker.
    with socket.socket() as probe:
        probe.bind(('127.0.0.1',args.port))
    metadata=dict(executable=str(broker),sha256=hashlib.sha256(broker.read_bytes()).hexdigest(),plugin_sha256=hashlib.sha256(plugin.read_bytes()).hexdigest(),version=subprocess.run([str(broker),'-h'],capture_output=True,text=True).stdout,qos=1,port=args.port,host='127.0.0.1')
    (OUT/'version.json').write_text(json.dumps(metadata,indent=2))
    rows=[]
    snapshots=[json.loads((ROOT/f'results/round2/raw/C{x}-0_declared_2_SPR2.json').read_text()) for x in [0,1,2,3,4,5]]
    snapshots.append(json.loads((ROOT/'results/round2/raw/C0-0_minimal_2_SPR2.json').read_text()))
    for snapshot in snapshots:
      task=snapshot['task']; task=dict(task,id=task['id']+'_'+task['setting'])
      for phase in ['B0','SPR']:
        policy=task['policy'] if phase=='B0' else snapshot['policy']
        if policy is None:
            rows.append(dict(task=task['id'],phase=phase,status='no_repair',filter='',topic='',required='',suback='',delivered='',message_id=''));continue
        case=OUT/f"{task['id']}_{phase}";case.mkdir(exist_ok=True)
        security=case/'dynamic-security.json';security.write_text(json.dumps(config(policy),indent=2))
        conf=case/'mosquitto.conf';conf.write_text(f'listener {args.port} 127.0.0.1\nallow_anonymous false\npersistence false\nplugin {plugin.as_posix()}\nplugin_opt_config_file {security.as_posix()}\nlog_type all\nconnection_messages true\n')
        with (case/'broker.log').open('w') as log:
          proc=subprocess.Popen([str(broker),'-c',str(conf),'-v'],stdout=log,stderr=log)
          try:
            deadline=time.monotonic()+8
            while True:
              try:
                with socket.create_connection(('127.0.0.1',args.port),.2):break
              except OSError:
                if proc.poll() is not None or time.monotonic()>deadline:raise RuntimeError('broker startup failed; inspect broker.log')
                time.sleep(.1)
            for f in task['filters']:
              for topic in sorted(set(task['required']+task['forbidden'])):
                reader=MQTT(args.port,'reader');suback=reader.subscribe(f);pub=MQTT(args.port,'publisher')
                mid=f"{task['id']}:{phase}:{len(rows)}";pub.publish(topic,mid);messages=[]
                reader.s.settimeout(.2);end=time.monotonic()+.6
                while time.monotonic()<end:
                  try:
                    h,b=reader.packet()
                    if h>>4==3:
                      n=int.from_bytes(b[:2],'big');i=2+n;qos=(h>>1)&3
                      if qos:reader.send(0x40,b[i:i+2]);i+=2
                      messages.append(dict(topic=b[2:2+n].decode(),payload=b[i:].decode(),dup=bool(h&8)))
                  except socket.timeout:pass
                rows.append(dict(task=task['id'],phase=phase,status='observed',filter=f,topic=topic,required=topic in task['required'],suback=suback,delivered=sum(m['payload']==mid for m in messages),message_id=mid))
                with (case/'client.jsonl').open('a') as l:l.write(json.dumps(dict(**rows[-1],messages=messages))+'\n')
                reader.close();pub.close()
          finally:
            proc.terminate();proc.wait(timeout=5)
    with (OUT/'broker.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=rows[0].keys());w.writeheader();w.writerows(rows)
    (OUT/'status.json').write_text(json.dumps(dict(status='executed',rows=len(rows),scope='finite probes; timeout absence alone is not proof of denial'),indent=2))
    return 0

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--broker');p.add_argument('--plugin');p.add_argument('--port',type=int,default=28884);p.add_argument('--out')
    raise SystemExit(run(p.parse_args()))

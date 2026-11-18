"""Render through official draw.io Desktop, using an ASCII temporary staging path."""
from pathlib import Path
import argparse, hashlib, json, shutil, subprocess, tempfile
R=Path(__file__).resolve().parents[1];O=R/'figures/schematics_rich_20261103'
p=argparse.ArgumentParser();p.add_argument('names',nargs='*',default=['intro_problem','system_architecture']);a=p.parse_args()
stage=Path(tempfile.gettempdir())/'spr-iot-drawio-32.6.1';stage.mkdir(exist_ok=True)
app=stage/'app';source=R/'tools/drawio-portable/app'
if not (app/'draw.io.exe').exists():shutil.copytree(source,app,dirs_exist_ok=True)
assert hashlib.sha256((app/'draw.io.exe').read_bytes()).digest()==hashlib.sha256((source/'draw.io.exe').read_bytes()).digest()
log=[]
for name in a.names:
 assert name in ['intro_problem','system_architecture']
 shutil.copy2(O/(name+'.drawio'),stage/(name+'.drawio'))
 for fmt in ['png','svg','pdf']:
  out=name+'.'+fmt;cmd=[str(app/'draw.io.exe'),'--user-data-dir='+str(stage/'profile'),'--disk-cache-dir='+str(stage/'cache'),'--disable-gpu-shader-disk-cache','--export','--format',fmt,'--crop','--border','10','--output',out]
  if fmt=='png':cmd+=['--scale','2']
  cmd+=[name+'.drawio'];proc=subprocess.run(cmd,cwd=stage,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=45)
  assert proc.returncode==0 and (stage/out).stat().st_size>0,(cmd,proc.stdout,proc.stderr)
  shutil.copy2(stage/out,O/out);log.append(dict(figure=name,format=fmt,exit=proc.returncode,stdout=proc.stdout.strip(),stderr=proc.stderr.strip(),sha256=hashlib.sha256((O/out).read_bytes()).hexdigest()))
(O/'drawio_export_log.json').write_text(json.dumps(dict(renderer='Official draw.io Desktop 32.6.1',staging_reason='Project-path export timed out; ASCII-path export of identical XML succeeded.',runs=log),indent=2),encoding='utf8')
print(json.dumps(log,indent=2))

import subprocess,sys,time,pathlib
p=pathlib.Path(__file__).with_name('update.py')
while True:
 subprocess.run([sys.executable,str(p)],check=False)
 time.sleep(300)

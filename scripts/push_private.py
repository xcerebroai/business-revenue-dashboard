"""Push to the assigned private Sites source repo without persisting credentials."""
import getpass,json,os,subprocess,urllib.parse
credential=json.loads(getpass.getpass('Private source credential (hidden): '))
url=credential['remote_url'];branch=credential['branch'];token=credential['token']
assert urllib.parse.urlparse(url).scheme=='https'
assert not urllib.parse.urlparse(url).username
assert credential['auth_mode']=='http_extra_header'
assert url=='https://git.chatgpt-team.site/0d302269-481a-4d99-b8a7-f08261e7ec8c/appgprj_6aa864f591748191ac5f8604c71901f2.git', 'Unexpected Sites repository'
assert branch=='main' and credential['repository']=='appgprj_6aa864f591748191ac5f8604c71901f2', 'Unexpected Sites project or branch'
env=os.environ.copy();env.update(GIT_CONFIG_COUNT='1',GIT_CONFIG_KEY_0='http.extraHeader',GIT_CONFIG_VALUE_0='Authorization: Bearer '+token,GIT_TERMINAL_PROMPT='0')
result=subprocess.run(['git','push',url,'HEAD:refs/heads/'+branch],env=env,capture_output=True,text=True)
print(json.dumps({'push_succeeded':result.returncode==0,'exit_code':result.returncode,'detail':(result.stdout+result.stderr).replace(token,'[REDACTED]')[-2000:]}))
raise SystemExit(result.returncode)

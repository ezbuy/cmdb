from flask import Flask,request,jsonify
from crontab import CronTab
import commands
app = Flask(__name__)

@app.route('/',methods=['POST'])
def main():
    fun = request.json.get('fun')
    if fun == 'list':
        return jsonify({'result':get_crontab_list()})
    else:
        return jsonify({'result':0})

def get_crontab_list():
    cron = CronTab(tabfile='/etc/crontab',user=False)
    cron_list = []
    for info in cron[4:]:
        status,time = commands.getstatusoutput("grep '%s' /var/log/cron.log | tail -n 1 | awk \'{print $1,$2,$3}\'" % info.command)
        cron_list.append({str(info):time})
    return cron_list

if __name__ == '__main__':
    app.run(host='0.0.0.0',port=5000)
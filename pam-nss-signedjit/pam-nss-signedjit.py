#!/usr/bin/python3

import argparse
import json
from pprint import pprint
import shutil
import urllib
from subprocess import call
from datetime import datetime
import socket

parser = argparse.ArgumentParser(prog='pam-nss-signedjit')
subparsers = parser.add_subparsers(dest='subparser_name')
parser_update = subparsers.add_parser('update', help='update')
parser_bootstrap = subparsers.add_parser('bootstrap', help='bootstrap')
parser_bootstrap.add_argument('--filepath', help='filepath', required=True)
parser_sshkey = subparsers.add_parser('sshkey', help='sshkey lookup')
parser_sshkey.add_argument('--username', help='username', required=True)

args = parser.parse_args()

rootpath='/etc/pam-nss-signedjit/'
varpath='/var/lib/pam-nss-signedjit/'


def updatecerts():
    with open(rootpath+'cert.pem','w') as signing:
        for cert in data['certs']:
            signing.write(cert)
            signing.write('\n')

def updatejit():
    admins=[]
    jitusers=[]
    with open(varpath+"jitedusers","w") as jited:
        for h in data['jitbyhost']:
            if socket.gethostname() == h['host'] or h['host'] == '*':
                #pprint(h)
                if datetime.strptime(h['expiration'], "%Y-%m-%dT%H:%M:%SZ") > datetime.utcnow():
                    u=h['user']
                    jitusers.append(u)
                    if h['adminaccess'] == 1:
                        admins.append(u)
        jited.write('\n'.join(jitusers))
        jited.write('\n')

    with open(varpath+"passwd","w") as passwd:
        passent=[]
        for u in data['users']:
            uid=data['users'][u].get('uid',None)
            if(uid != None):
                shell=data['users'][u].get('shell','/bin/bash')
                passent.append(u+':*:'+str(uid)+':100:User:/home/'+u+':'+shell)
        passwd.write('\n'.join(passent))
        passwd.write('\n')

    with open(varpath+"group","w") as group:
        group.write("jitadmins:*:2000:"+(",".join(admins))+'\n')


if args.subparser_name == 'bootstrap':
    with open(args.filepath) as f:
        data = json.load(f)
        shutil.copy(args.filepath,rootpath+'validated.json')
    updatecerts()

with open(rootpath+'validated.json') as f:
    data = json.load(f)

#pprint(args)

if args.subparser_name == 'sshkey':
    print(data['users'].get(args.username,{'keys':''}).get('keys',None))


if args.subparser_name == 'update':
    for url in data['urls']:
        urllib.urlretrieve (url, varpath+"temp.signed")
        ret=call(["openssl","cms","-verify","-in",varpath+"temp.signed","-inform","pem","-out",varpath+"signedtext.json.gz","-certfile",rootpath+"cert.pem","-noverify","-nointern"])
        if ret == 0:
            signcount=0
            with open() as signers:
                signercerttext=signers.read().split("-\n-")
                finalsignercerts=[]
                for i, v in enumerate(signercerttext):
                    if i == 0:
                        c=v+"-"
                    elif i < len()-1:
                        c="-"+v+"-"
                    else:
                        c="-"+v
                    finalsignercerts.append(c)
                signcount=len(set(data['certs']).intersection(finalsignercerts))
            if signcount>=data['numsigsreq']:
                ret2=call(["gunzip","-f",varpath+"signedtext.json.gz"])
                if ret2 == 0:
                    with open(varpath+"signedtext.json") as st:
                        stjson = json.load(st)
                        if stjson['serial'] > data['serial']:
                            shutil.copy(varpath+"signedtext.json",rootpath+'validated.json')
                            data=stjson
                            updatecerts()
                        updatejit()

if __name__ == '__main__':
    sys.exit(main())
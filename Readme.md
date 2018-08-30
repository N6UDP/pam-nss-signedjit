# pam-nss-signedjit

## About

pam-nss-signedjit reads a signed (via [CMS](https://en.wikipedia.org/wiki/Cryptographic_Message_Syntax)) file from an HTTPS endpoint and applies the file to local NSS and PAM files for the purposes of enabling Just-in-Time (JIT) administration.

It intended to be used with:

* ssh keys via AuthorizedKeysCommand
* PAM listfile for authorization / JIT
* NSS extrausers for user and group (admin / sudoers group) info
* pam_mkhomedir for homedir creation

## Install instructions

***First*** make a bootstrap.json and also a signed json file uploaded to the url in bootstrap.json.  This can be done either via:
* openssl

```
gzip bootstrap.example.json
openssl cms -sign -in cat bootstrap.example.json.gz -text -outform pem -out jit.signed -signer acert.pem
```

* via `certsign.ps1`

It can be validated with either powershell/.NET CMS or via openssl:

```
openssl cms -verify -in jit.signed -inform pem -out bootstrap.example.json.gz -certfile acert.pem -noverify -nointern
gunzip bootstrap.example.json.gz
```

Next on client machines:

1. `cp pam-nss-signedjit /usr/local/bin/pam-nss-signedjit`
2. `mkdir /var/lib/pam-nss-signedjit && mkdir /etc/pam-nss-signedjit`
3. `/usr/local/bin/pam-nss-signedjit bootstrap --filepath bootstrap.json`
4. `apt install libnss-extrausers`
5. `ln -s /var/lib/pam-nss-signedjit/passwd /var/lib/extrausers/passwd && ln -s /var/lib/pam-nss-signedjit/group /var/lib/extrausers/group`
6. edit /etc/nsswitch.conf adding

```
   passwd:         compat extrausers
   group:          compat extrausers
```

7. Add the following to /etc/ssh/sshd_config:

```
AuthorizedKeysCommand /usr/local/bin/pam-nss-signedjit sshkey --username %u
AuthorizedKeysCommandUser nobody
```

8. Add a crontab entry `* * * * * /usr/local/bin/pam-nss-signedjit update 2>/dev/null >/dev/null`
9. Add a sudoers entry `%jitadmins ALL=(ALL) NOPASSWD: ALL`
10. Add a common-auth entry `auth    requisite      pam_listfile.so item=user sense=allow file=/var/lib/pam-nss-signedjit/jitedusers onerr=fail`
    * If you want separate break-glass allow list you can use `[success=1 default=ignore]` instead of `requisite` and a second pam_listfile.so line with `requisite`
11. Add a common-session entry `session required    pam_mkhomedir.so skel=/etc/skel/ umask=0022`
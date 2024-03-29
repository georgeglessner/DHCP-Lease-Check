from credentials import SERVER, USER, PASSWORD, G_USER, G_PASS, G_TO
from email.message import EmailMessage
import paramiko
import smtplib
import re
import os

# connect and execute ssh commands
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(SERVER, username=USER, password=PASSWORD)
stdin, stdout, ssh_stderr = ssh.exec_command("cat /tmp/dnsmasq.leases")

# get current leases from ssh command
leases = stdout.read().decode("utf-8")
stdin.flush()
ssh.close()

# check to see if leaseList.txt exists
# create file if it doesn't
if not os.path.exists("./leaseList.txt"):
    open("leaseList.txt", "a").close()

# initialize current leases array
currentLeases = []

# get current leases MAC addresses
# add to currentLeases array
for lease in leases.split("\n"):
    if len(lease) > 0:
        leaseCheck = re.compile("(?:[0-9a-fA-F]:?){12}")
        activeLeases = re.findall(leaseCheck, lease)
        currentLeases.append("{} : {}".format(activeLeases[0], lease.split()[3]))

# add current leases to leaseList.txt if empty
if os.stat("leaseList.txt").st_size == 0:
    with open("leaseList.txt", "w") as w:
        for lease in currentLeases:
            if len(lease) > 0:
                w.write("{}\n".format(lease))
    w.close()

# create lease list array from leaseList.txt
leaseList = [line.rstrip("\n") for line in open("leaseList.txt")]

# clear out the current lease list
with open("leaseList.txt", "w"):
    pass


# find any new leases, add to array
# add new leases to leaseList.txt
newLeases = []
with open("leaseList.txt", "w") as f:
    for lease in currentLeases:
        f.write("{}\n".format(lease))
        if (len(lease) > 0) and (lease not in leaseList):
            newLeases.append(lease)
f.close()


# send e-mail with new leases
if len(newLeases) > 0:
    # set up message
    msg = EmailMessage()
    msg["Subject"] = "New DHCP Leases Found"
    msg["From"] = G_USER
    msg["To"] = G_TO
    msg.set_content(str(newLeases))

    # send message
    s = smtplib.SMTP("smtp.gmail.com", 587)
    s.starttls()
    s.login(G_USER, G_PASS)
    s.send_message(msg)
    s.quit()

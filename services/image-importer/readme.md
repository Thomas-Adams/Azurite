```bash

sudo mount -t cifs //192.168.178.45/D:/ /mnt/windows/stablediffusion \
  -o credentials=/home/tadams/.smbcredentials,uid=$(id -u),gid=$(id -g)

```
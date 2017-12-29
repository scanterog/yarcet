#!/bin/sh -e

user="test"
grep "${user}:" /etc/passwd
if [ $? -eq 1 ]; then
  echo "user $user does not exist, creating it."
  adduser --disabled-password --gecos '' $user
  echo "$user ALL=(ALL) NOPASSWD: ALL" >> /etc/sudoers.d/sudoers
  mkdir -p /home/$user/.ssh/
  cat > /home/$user/.ssh/authorized_keys << EOF
# insert your key here
EOF
  chown -R $user:$user /home/$user/.ssh
else
  echo "$user already exist. Skipping creation."
fi

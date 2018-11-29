#!/bin/bash

#######################################################################
#   Get nds versions by ssh'g into provided host as root
#
#   Written by Ken Shaffer
#######################################################################

#######################################################################
#   The help
#######################################################################
usage() {
    me=`basename $0`
    cat <<EOF >&2

$me  [ ssh_options ]  host_ip  [ another_ip ... ]

ssh to each host, perform ls of /opt/nds and /opt/web to get versions

You will be prompted for passwords multiple times if you don't have an
ssh key established. 

You should pass the -i option pointing to a private key, the corresponding
public key of which is an entry in the users .ssh/authorized_keys file.

The default ssh user is set via the option "-l root". You may of course
pass in another -l option if using a different user account, but the
user chosen must be a valid user on every host passed on the command
line.

EOF
}

#######################################################################
# if want help, provide it
#######################################################################
if [ "$1" = "-?" -o "$1" = "-h" -o -z "$1" ]; then
    usage
    exit 1
fi

MY_SSH_OPTS="-l root"

#######################################################################
# parse ssh options
#######################################################################
while getopts ":1246AaCfgKkMNnqsTtVvXxYyb:c:D:e:F:i:L:l:m:O:o:p:R:S:W:w:" c; do
    if [[ "1246AaCfgKkMNnqsTtVvXxYy" =~ "$c" ]]; then
        MY_SSH_OPTS="$MY_SSH_OPTS -${c}"
    elif [[ "bcDeFiLlmOopRSWw" =~ "$c" ]]; then
        MY_SSH_OPTS="$MY_SSH_OPTS -${c} ${OPTARG}"
    elif [[ ":?" =~ "$c" ]]; then
        echo
        echo "Invalid ssh option passed" >&2
        usage
        exit 1
    fi
done
shift $((OPTIND - 1))
if [ "$1" = "-?" -o "$1" = "-h" -o -z "$1" ]; then
    usage
    exit 1
fi
#######################################################################
# ssh into each host and do the listing required
#######################################################################
(
while [ -n "$1" ]; do
    ssh $MY_SSH_OPTS $1 'cd /opt/nds 2>/dev/null||exit 1;ls |xargs -L 1 readlink;exit 0'
    ssh $MY_SSH_OPTS $1 'cd /opt/web 2>/dev/null||exit 1;ls |xargs -L 1 readlink;exit 0'
    shift
done
) | sort -fu

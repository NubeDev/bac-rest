DEFAULT="\033[0m"
GREEN="\033[32m"
RED="\033[31m"

USER=""
WORKING_DIR=""
SERVICE=nubeio-bac-rest.service
SERVICE_DIR=/lib/systemd/system
SERVICE_DIR_SOFT_LINK=/etc/systemd/system/multi-user.target.wants
COMMAND=""

help() {
    echo "Service commands:"
    echo -e "   ${GREEN}start -u=<user> -dir=<working_dir>${DEFAULT}        Start the service (-u=pi -dir=/home/pi/backend-${version}-${sha})"
    echo -e "   ${GREEN}disable${DEFAULT}                                   Disable the service"
    echo -e "   ${GREEN}enable${DEFAULT}                                    Enable the stopped service"
    echo -e "   ${GREEN}delete${DEFAULT}                                    Delete the service"
    echo -e "   ${GREEN}restart${DEFAULT}                                   Restart the service"
    echo
    echo "Service parameters:"
    echo -e "   ${GREEN}-h --help${DEFAULT}                                 Show this help"
    echo -e "   ${GREEN}-u --user=<user>${DEFAULT}                          Which <user> is starting the service"
    echo -e "   ${GREEN}-dir --working-dir=<working_dir>:${DEFAULT}         From where wires is starting"
}
start() {
    if [[ ${USER} != "" && ${WORKING_DIR} != "" ]]
    then
        echo -e "${GREEN}Install service packages${DEFAULT}"
        sudo apt-get update
        sudo apt-get install build-essential python-dev python-setuptools python3-pip python3-pip virtualenv -y
        pip install -U pip setuptools wheel
        rm -r venv
        python3 -m venv venv
        source venv/bin/activate
        pip3 install -r requirements.txt
        deactivate

        echo -e "${GREEN}Creating Linux Service${DEFAULT}"
        sudo cp systemd/${SERVICE} ${SERVICE_DIR}/${SERVICE}
        sed -i -e 's/<user>/'"${USER}"'/' ${SERVICE_DIR}/${SERVICE}
        sed -i -e 's,<working_dir>,'"${WORKING_DIR}"',' ${SERVICE_DIR}/${SERVICE}

        echo -e "${GREEN}Soft Un-linking Linux Service${DEFAULT}"
        sudo unlink ${SERVICE_DIR_SOFT_LINK}/${SERVICE}

        echo -e "${GREEN}Soft Linking Linux Service${DEFAULT}"
        sudo ln -s ${SERVICE_DIR}/${SERVICE} ${SERVICE_DIR_SOFT_LINK}/${SERVICE}

        
        echo -e "${GREEN}Enabling Linux Service${DEFAULT}"
        sudo systemctl daemon-reload
        sudo systemctl enable ${SERVICE}

        echo -e "${GREEN}Starting Linux Service${DEFAULT}"
        sudo systemctl start ${SERVICE}

        echo -e "${GREEN}Service is created and started, please reboot to confirm...${DEFAULT}"
    else
        echo -e ${RED}"-u=<user> -dir=<working_dir> these parameters should be on you input (-h, --help for help)${DEFAULT}"
    fi
}

disable() {
    echo -e "${GREEN}Stopping Linux Service${DEFAULT}"
    sudo systemctl stop ${SERVICE}
    echo -e "${GREEN}Disabling Linux Service${DEFAULT}"
    sudo systemctl disable ${SERVICE}
    echo -e "${GREEN}Service is disabled...${DEFAULT}"
}

enable() {
    echo -e "${GREEN}Enabling Linux Service${DEFAULT}"
    sudo systemctl enable ${SERVICE}
    echo -e "${GREEN}Starting Linux Service${DEFAULT}"
    sudo systemctl start ${SERVICE}
    echo -e "${GREEN}Service is enabled...${DEFAULT}"
}

delete() {
    echo -e "${GREEN}Stopping Linux Service${DEFAULT}"
    sudo systemctl stop ${SERVICE}
    echo -e "${GREEN}Un-linking Linux Service${DEFAULT}"
    sudo unlink ${SERVICE_DIR_SOFT_LINK}/${SERVICE}
    echo -e "${GREEN}Removing Linux Service${DEFAULT}"
    sudo rm -r ${SERVICE_DIR}/${SERVICE}
    echo -e "${GREEN}Service is deleted...${DEFAULT}"
}

restart() {
    echo -e "${GREEN}Restarting Linux Service${DEFAULT}"
    sudo systemctl restart ${SERVICE}
    echo -e "${GREEN}Service is restarted...${DEFAULT}"
}

parseCommand() {
    for i in "$@"
    do
    case ${i} in
    -h|--help)
        help
        exit 0
        ;;
    -u=*|--user=*)
        USER="${i#*=}"
        ;;
    -dir=*|--working-dir=*)
        WORKING_DIR="${i#*=}"
        ;;
    start|disable|enable|delete|restart)
        COMMAND=${i}
        ;;
    *)
        echo -e "${RED}Unknown option (-h, --help for help)${DEFAULT}"
        exit 1
        ;;
    esac
    done
}


runCommand() {
    case ${COMMAND} in
    start)
        start
        ;;
    disable)
        disable
        ;;
    enable)
        enable
        ;;
    delete)
        delete
        ;;
    restart)
        restart
        ;;
    esac
}

parseCommand "$@"
runCommand
exit 0
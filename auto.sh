#!/bin/bash

export WORKSPACE=$(find $HOME -name "todo-flask-app")

change_docker_permission(){
    sudo chmod 666 /var/run/docker.sock
    ls -l /var/run/docker.sock
}

install_depen_all(){

    sys=$1

    if [[ $sys == "" ]]; then
        echo "Please provide system to install (debian, ubuntu, rhel,...)"
        return
    fi

    if [[ $sys == "debian" || $sys == "ubuntu" ]]; then
        sudo apt update && sudo apt-get install -y git curl vim ca-certificates python3 python3-pip
        # Add Docker's official GPG key:
        sudo install -m 0755 -d /etc/apt/keyrings
        sudo curl -fsSL https://download.docker.com/linux/$sys/gpg -o /etc/apt/keyrings/docker.asc
        sudo chmod a+r /etc/apt/keyrings/docker.asc

        # Add the repository to Apt sources:
        echo \
        "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/$sys \
        $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
        sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
        sudo apt-get update
        sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
        change_docker_permission
    else
        echo "This is not support for $sys, Please waite!"
        return
    fi

}

setup(){
    # cp .env.example > .env
    export SECRET_KEY=""
    JWT_SECRET_KEY=""
    SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))")
    JWT_SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))")
    printf "SECRET_KEY=$SECRET_KEY\n" > ${WORKSPACE}/.env
    printf "JWT_SECRET_KEY=$JWT_SECRET_KEY\n" >> ${WORKSPACE}/.env
    cat ${WORKSPACE}/.env.example >> ${WORKSPACE}/.env
}


## docker compose build --no-cache web
## docker compose --env-file .env up
    
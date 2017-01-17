#!/bin/sh

set -e

retention_duration="86400"
keep_containers=""
keep_tags=""
tryrun=0
debug=0

usage() {
    cat <<-EOF
		Usage: $0 [OPTIONS]
		    [-r|--retention VALUE]    	Retention duration in seconds (default: $retention_duration)
		    [-c|--keep-container NAME]	Keep this named container
		    [-i|--keep-image NAME]    	Keep this tagged image
		    [-n]                      	Don't remove anything

		    [-d|--debug]              	Run with debug and verbose flags (-xv)
		    [-h|--help]               	Print this help and exit
	EOF

}

OPTS=$(getopt -n $0 -o "r:c:i:ndh" \
              --long "retention:,keep-container:,keep-image:,debug,help" \
              -- "$@")

if [ $? -ne 0 ]; then
    exit 1
fi

eval set -- "$OPTS"

while true; do
    case "$1" in
        -r|--retention)
            retention_duration="$2"
            shift 2
            ;;
        -c|--keep-container)
            keep_containers="$keep_containers $2"
            shift 2
            ;;
        -i|--keep-image)
            case "$2" in
                *:*) tag="$2" ;;
                *) tag="$2:latest" ;;
            esac
            keep_tags="$keep_tags $tag"
            shift 2
            ;;
        -n)
            tryrun=1
            shift
            ;;
        -d|--debug)
            debug=1
            shift
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        --)
            shift
            if [ $# -gt 0 ]; then
                echo "Warning: Ignoring arguments \"$@\"" >&2
            fi
            break
            ;;
        *)
            echo "Error: Argument invalid: $1" >&2
            exit 1
            ;;
    esac
done

if [ $debug -eq 1 ]; then
    set -xv
fi

#
# Function to increment the warnings counter
#

warnings_count=0
incr_warnings() {
    warnings_count="$(($warnings_count + 1))"
}

#
# Compute the timestamp limit
#

now="$(date +%s)"
before="$(($now - $retention_duration))"

#
# List all containers and images
#

echo "List of all containers:"
echo "-----------------------"
docker ps --all --size --no-trunc
echo

echo "List of all images:"
echo "-------------------"
docker images --no-trunc
echo

echo "List of all volumes:"
echo "--------------------"
docker volume ls
echo

#
# Remove old containers
#

for cid in $(docker ps --all --quiet); do
    ts="$(docker inspect --format '{{ .Created }}' $cid | xargs -r date +%s -d)"
    if [ -z "$ts" ]; then
        continue
    fi

    if [ $ts -ge $before ]; then
        continue
    fi

    cname="$(docker inspect --format '{{ .Name }}' $cid)"
    if [ -n "$keep_containers" ]; then
        for keep_container in $keep_containers; do
            if [ "/$keep_container" = "$cname" ]; then
                continue 2
            fi
        done
    fi

    echo "Removing container ${cname##/} ($cid)..."
    if [ $tryrun -eq 0 ]; then
        if ! docker rm --force --volumes "$cid"; then
            incr_warnings
        fi
    fi
done

#
# Autodelete volumes from stuck containers
#

for vid in $(docker volume ls --quiet --filter dangling=true); do
    case "$vid" in
        AUTODELETE*) ;;
        *)
            continue
            ;;
    esac

    echo "Removing volume $vid..."
    if [ $tryrun -eq 0 ]; then
        if ! docker volume rm "$vid"; then
            incr_warnings
        fi
    fi
done

#
# Remove old images
#

for iid in $(docker images --quiet | uniq); do
    ts="$(docker inspect --format '{{ .Created }}' $iid | xargs -r date +%s -d)"
    if [ -z "$ts" ]; then
        continue
    fi

    if [ $ts -ge $before ]; then
        continue
    fi

    tags="$(docker inspect --format '{{join .RepoTags " "}}' $iid)"
    if [ -n "$tags" ]; then
        remove_tags=
        if [ -n "$keep_tags" ]; then
            for tag in $tags; do
                for keep_tag in $keep_tags; do
                    if [ $keep_tag = $tag ]; then
                        continue 2
                    fi
                done

                if [ -z "$remove_tags" ]; then
                    remove_tags="$tag"
                else
                    remove_tags="$remove_tags $tag"
                fi
            done
        else
            remove_tags="$tags"
        fi

        if [ -z "$remove_tags" ]; then
            continue
        fi

        echo "Removing tags $remove_tags ($iid)..."
        rid="$remove_tags"
    else
        echo "Removing image $iid..."
        rid="$iid"
    fi

    if [ $tryrun -eq 0 ]; then
        if ! docker rmi --force $rid; then
            incr_warnings
        fi
    fi
done

#
# Exit 2 if warnings else 0
#

if [ $warnings_count -gt 0 ]; then
    exit 2
else
    exit 0
fi

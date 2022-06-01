#! /bin/sh

repos=('activemq' 'ant' 'camel' 'derby' 'geronimo' 'hbase' 'hadoop' 'ant-ivy' 'jackrabbit' 'jmeter' 'logging-log4j2' 'lucene' 'mahout' 'openjpa' 'pig' 'poi' 'velocity-engine' 'xerces-c')

chmod +x stats.py
files="src/JiTReliablity_Results/*.json"
i=0

for f in $files 
do
    if [ -f "$f" ]
    then
        echo "Using $f"
        repo=${repos[$i]}
        git clone https://github.com/apache/$repo.git

        chmod -R 777 "${repo}"

        python stats.py --repo_path "${repo}"

        rm -rf $repo

	i=($i+1)
    else
        echo "Warning: Some problem with \"$f\""
    fi
done

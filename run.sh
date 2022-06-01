#! /bin/sh

repos=('activemq' 'ant' 'camel' 'derby' 'geronimo' 'hbase' 'hadoop' 'ant-ivy' 'jackrabbit' 'jmeter' 'logging-log4j2' 'lucene' 'mahout' 'openjpa' 'pig' 'poi' 'velocity-engine' 'xerces-c')

chmod +x src/code/scripts/commits_to_neo.py
i=0
flag=14
files="src/JiTReliablity_Results/*.json"

for f in $files 
do
    if [ -f "$f" ]
    echo "Using $f"
    then
        if [ $i -ge $flag ]
        then
            repo=${repos[$i]}
            git clone https://github.com/apache/$repo.git

            outfile="src/Neo4j_output/Jit_Reliability_Output/Out_${i}.csv"
            python src/code/scripts/commits_to_neo.py --repo_path "${repo}" --fip "${f}" --outfile "${outfile}"

            rm -rf $repo
            i=$(( i + 1 ))
        else
            i=$(( i + 1 ))
        fi
    else
        echo "Warning: Some problem with \"$f\""
    fi
done
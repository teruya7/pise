#!/bin/bash

name="$1"
functional="$2"

#利用しているスパコンを指定
system=ito

if [ $system = ito]; then
    num_jobs=$(pjstat |awk '{print $10}'| awk 'NR==3')
    limit_jobs=128
    submit_command=pjsub
elif [ $system = laurel]; then
    num_jobs=$(qgroup | grep Nagafuji | awk '{print$6}' | sed 's/[(]//g')
    limit_jobs=1800
    submit_command=sbatch
fi

function submission(){
    if [ -d $1 ]; then
        cd $1
        for i in */
        do
            if [ $num_jobs -ge $limit_jobs ]; then
                echo "The maximum number of calculations has been reached."
                break
            fi

            echo $i
            cd $i
            if [ -e ready_for_submission.txt ]; then
                $submit_command run6.4.1_*.sh
                rm ready_for_submission.txt
            else
                echo "no ready_for_submission.txt"
            fi
            cd ../
        done
        cd ../
    fi
}

cd "$name"/"$functional"/

submission unitcell
submission cpd
submission defect

for i in dopant_*/ 
do 
    cd $i
    submission cpd
    submission defect
    cd ../
done

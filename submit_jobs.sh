#!/bin/bash

name="$1"
functional="${2:-pbesol}"

source "$HOME"/pise/conf.txt

if [ $system = ito ]; then  
    limit_jobs=128
    submit_command=pjsub
elif [ $system = laurel ]; then
    num_jobs=$(qgroup | grep Nagafuji | awk '{print$6}' | sed 's/[(]//g')
    limit_jobs=1800
    submit_command=sbatch
fi

function submission(){
    if [ -d $1 ]; then
        cd $1
        for i in */
        do
            if [ $system = ito ]; then  
                num_jobs=$(pjstat |awk '{print $10}'| awk 'NR==3')
            elif [ $system = laurel ]; then
                num_jobs=$(qgroup | grep Nagafuji | awk '{print$6}' | sed 's/[(]//g')
            fi
            
            echo $num_jobs
            if [ $num_jobs -ge $limit_jobs ]; then
                echo "The maximum number of calculations has been reached."
                break
            fi

            echo $i
            cd $i
            if [ -e ready_for_submission.txt ]; then
                if [ -e WAVECAR ]; then
                    $submit_command $job_script_name_4
                    rm ready_for_submission.txt
                else
                    $submit_command $2
                    rm ready_for_submission.txt
                fi
            else
                echo "no ready_for_submission.txt"
            fi
            cd ../
        done
        cd ../
    fi
}

cd "$name"/"$functional"/

# submission unitcell $job_script_name_1
# submission cpd $job_script_name_1
submission defect $job_script_name_4

for i in dopant_*/ 
do 
    cd $i
    # submission cpd $job_script_name_1
    submission defect $job_script_name_4
    cd ../
done

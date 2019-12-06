#README comsm0010_CW

## Tristan Warren - tw15212

This is the Clound Nonce Discovery System (CND) running on AWS

##Installation Instructions

+ Store AWS private key in ``~/.aws/credentials``

+ Store config details in ``~/.aws/config``

+ Install pip on local machine

+ In project directory run

        $ pip install virtualenv
        $ virtualenv cloudVenv
        $ source cloudVenv/bin/activate
        $ pip install boto3

+ Create and launch t2.micro Amazon Linux 2 Instance using same private key and leaving everything else as default

+ SSH into instance and use CLI in the home directory to run

        $ sudo yum install python3 -y
        $ curl -O https://bootstrap.pypa.io/get-pip.py
        $ sudo python3 get-pip.py
        $ sudo pip install virtualenv --user
        $ virtualenv cndVenv
        $ source cndVenv/bin/activate
        $ pip install boto3

+ Copy ``cnd.py`` to home directory of instance

+ Create directory ``~/.aws/``

+ Store AWS private key in ``~/.aws/credentials``

+ Store config details in ``~/.aws/config``

+ Create image from instance

+ Replace ami string on line 116 in ``cnd_master.py`` with the AMI ID of the new image

+ Run CND system using ``python3 cnd_master`` using the following command line arguments to specify behaviour 

####Command Line Arguments:

    --n --nodes
    Description:	Number of instances to run
	Default:	1

    --d  --difficulty
    Description:	Difficulty of Nonce Discovery
	Default:	20

    --r  --random
    Description:	Random Block to be hashed (default: "COMSM0010cloud")
	Default:	False

    --l  --length
    Description:	Length of random block to hash
	Default:	14

    --t  --maxtime
    Description:	Maximum runtime (seconds) of CND (if 0 then no run time limit)
	Default:	600

    --l  --length
    Description:	Length of random block to hash
	Default:	14

    --c  --cost
    Description:	Show ongoing costs whilst running (0 for no costs)
	Default:	5

    --sc  --scramcost
    Description:	Scram after certain cost ($) is exceeded (Default 0 = no limit)
	Default:	0

    --dt  --desiredtime
    Description:	Desired Run Time (Default 0 = no desired run time), overwites desired number of instances
	Default:	0

    --dc  --desiredconfidence
    Description:	Desired Run Time Confidence
	Default:	90

####Keyboard Interupt:

    Keyboard inturpt will scram instances and clear queues
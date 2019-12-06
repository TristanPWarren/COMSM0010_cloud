#!/usr/bin/env python3
#Cloud Nonce Discovery - master tw15212
from hashlib import sha256
import time
import argparse
import math
import boto3
import random
import sys
from botocore.exceptions import ClientError

parser = argparse.ArgumentParser(
    description="Clound Nonce Discovery",
    formatter_class=argparse.ArgumentDefaultsHelpFormatter,
)

parser.add_argument(
    "--n",
    "--nodes",
    default=1,
    type=int,
    help="Number of instances",
)

parser.add_argument(
    "--d",
    "--difficulty",
    default=20,
    type=int,
    help="Difficulty in nonce discovery",
)

parser.add_argument(
    "--l",
    "--length",
    default=14,
    type=int,
    help="Length of Hash",
)

parser.add_argument(
    "--t",
    "--maxtime",
    default=600,
    type=int,
    help="Max runtime (seconds) of CND (if 0 then no run time limit)",
)

parser.add_argument(
	"--r",
	"--random",
	action='store_true',
	help="Random Block to be Hashed (default: COMSM0010cloud)"
)

parser.add_argument(
    "--c",
    "--cost",
    default=5,
    type=int,
    help="Show costs whilst running (if 0 no costs are show)",
)

parser.add_argument(
    "--sc",
    "--scramcost",
    default=0,
    type=float,
    help="Scram after certain cost ($) is exceeded (Default 0 = no limit)",
)

parser.add_argument(
    "--dt",
    "--desiredtime",
    default=0,
    type=int,
    help="Desired Run Time (s) (Default 0 = no desired run time), overwites desired number of instances",
)

parser.add_argument(
    "--dc",
    "--desiredconfidence",
    default=90,
    type=int,
    help="Desired Run Time Confidence (%)",
)


args = parser.parse_args()


def main(args):
	# Set max run time
	if args.t <= 0:
		max_run_time = 9999999999
	else:
		max_run_time = args.t

	# Set difficulty
	difficulty = args.d

	# Set number of instances
	if args.dt > 0:
		x_ = - math.log(1 - (args.dc/100))
		t_ = 2.09e-7 * (2 ** (difficulty - 1))
		n = (t_ * x_) / args.dt

		number_of_instances = math.ceil(n)
	else:
		number_of_instances = args.n

	# Set length of hash
	length_of_hash = args.l

	# Define variables
	image_id = 'ami-0982c6389a85a976e' ###REPLACE
	userData = """#!/bin/bash
	export HOME=/home/ec2-user/
	cd /home/ec2-user/
	source cndVenv/bin/activate
	python3 cnd.py"""
	queue_out_name = "nonce_discovery_out"
	queue_in_name = "nonce_discovery_in"
	nonce_range = math.floor(4294967296 / number_of_instances)

	if args.r:
		block_to_hash = ""
		for i in range(length_of_hash):
			block_to_hash += (chr(random.randint(97,122)))
	else:
		block_to_hash = "COMSM0010cloud"

	print("")
	print(f'Block to Hash:   {block_to_hash}')

	start_time = time.time()

	# Get nonce queues
	sqs = boto3.resource('sqs')
	sqs.create_queue(QueueName="nonce_discovery_out")
	sqs.create_queue(QueueName="nonce_discovery_in")
	queue_out = sqs.get_queue_by_name(QueueName=queue_out_name)
	queue_in = sqs.get_queue_by_name(QueueName=queue_in_name)

	# Start Instances
	ec2 = boto3.resource('ec2')
	instances = ec2.create_instances(ImageId=image_id, InstanceType='t2.micro', MaxCount=number_of_instances, MinCount=number_of_instances, Monitoring={'Enabled': True}, UserData=userData, KeyName='nonce_discovery')




	# Send instructions to queue
	for instance in range(number_of_instances):
		instance_lower = instance * nonce_range
		instance_higher = ((instance + 1) * nonce_range) - 1
		response = queue_out.send_message(MessageBody=f'{instance}', MessageAttributes={
				'Difficulty': {
					'StringValue': str(difficulty),
					'DataType': 'String',
				},
				'LowerRange': {
					'StringValue': str(instance_lower),
					'DataType': 'String',
				},
				'UpperRange': {
					'StringValue': str(instance_higher),
					'DataType': 'String',
				},
				'Block': {
					'StringValue': str(block_to_hash),
					'DataType': 'String',
				},  
			})



	
	try:
		scramBool = False

		# Whilst running
		messages = []
		cost_time = 0
		cost = 0
		while len(messages) < 1:
			# Check for completion
			for newMessage in queue_in.receive_messages(MaxNumberOfMessages=1, MessageAttributeNames=['ElapsedTime', 'Nonce', 'NonceBinary']):
				messages.append(newMessage)

			# Scram after running for too long
			if (time.time() - start_time) > max_run_time:
				scramBool = True
				print("")
				print("")
				print("*******************************************")
				print("Max run time exceeded - Scramming Instances")
				print("*******************************************")
				break

			current_time = time.time()
			a = 0

			# Get update instance data
			instances[0].reload()

			if instances[0].state["Code"] == 16:
				if cost_time == 0:
					cost_time = time.time()
				
				if time.time() - cost_time < 60:
					a = (0.0116/3600) * 60 * args.n
				else:
					a = ((0.0116/3600) * (time.time()-cost_time)) * args.n
	
				cost = '{:.10f}'.format(a)

				# Show cost of running
				if (current_time - cost_time) > args.c:
					sys.stdout.write(f'\rEstimated cost:  ${cost}     Estimated Running Time: {time.time() - cost_time}')

			else:
				sys.stdout.write(f'\rEstimated cost:  $0 - Starting Up')

			# Scram if cost is too high
			if (float(cost) > args.sc) and (args.sc > 0):
				print("")
				print("")
				print("**********************************")
				print("Cost Overrun - Scramming Instances")
				print("**********************************")
				scramBool = True



			# Only check messages every second
			time.sleep(1)


		if scramBool:
			scram(instances, queue_in, queue_out, sqs)

		else:
			# Recieve Messages
			elapsedTime = float(messages[0].message_attributes.get('ElapsedTime').get('StringValue'))
			nonce = str(messages[0].message_attributes.get('Nonce').get('StringValue'))
			nonceBinary = str(messages[0].message_attributes.get('NonceBinary').get('StringValue'))

			end_time = time.time()

			print("")
			print("")
			print(f'Difficulty:      {difficulty}')
			print(f'Elapsed Time:    {elapsedTime}')
			print(f'Nonce:           {nonce}')
			print(f'Nonce Binary:    {nonceBinary}')
			print(f'Time in cloud:   {elapsedTime}')
			print(f'Total time:      {end_time - start_time}')
			print(f'Cost:            ${cost}')

			scram(instances, queue_in, queue_out, sqs)

	# If keyboard inturrupt pressed		
	except KeyboardInterrupt:
		print("")
		print("")
		print("**************************************")
		print('Keyboard Interrupt: Scramming Instances')
		print("***************************************")
		scram(instances, queue_in, queue_out, sqs)



# Close instances
def scram(instances, queue_in, queue_out, sqs):	
	for instance in instances:
		instance.terminate()

	# Purge Queues
	queue_in.purge()
	queue_out.purge()

	clientSQS = boto3.client('sqs')
	clientSQS.delete_queue(QueueUrl=queue_in.url)
	clientSQS.delete_queue(QueueUrl=queue_out.url)



if __name__ == "__main__":
	main(parser.parse_args())
	

#!/usr/bin/env python3
#Cloud Nonce Discovery - tw15212
from hashlib import sha256
import time
import boto3
from botocore.exceptions import ClientError

# Constants
block_to_hash = "COMSM0010cloud"
queue_in_name = "nonce_discovery_out"
queue_out_name = "nonce_discovery_in"

# From messgages
nonce_lower = 0
nonce_upper = 1
difficulty = 20


# Get nonce queues
sqs = boto3.resource('sqs')
queue_in = sqs.get_queue_by_name(QueueName=queue_in_name)
queue_out = sqs.get_queue_by_name(QueueName=queue_out_name)


#Get difficulty and nonce ranges
messages = []
while len(messages) < 1:
	for newMessage in queue_in.receive_messages(MaxNumberOfMessages=1, MessageAttributeNames=['Difficulty', 'LowerRange', 'UpperRange', 'Block']):
		messages.append(newMessage)

difficulty = int(messages[0].message_attributes.get('Difficulty').get('StringValue'))
nonce_lower = int(messages[0].message_attributes.get('LowerRange').get('StringValue'))
nonce_upper = int(messages[0].message_attributes.get('UpperRange').get('StringValue'))
block_to_hash = str(messages[0].message_attributes.get('Block').get('StringValue'))

messages[0].delete()




# Calculate Nonce
block_as_bin = ""
for char in block_to_hash:
	block_as_bin += '{:08b}'.format(ord(char))

searching = True
nonce = nonce_lower

start_time = time.time()
while nonce <= nonce_upper:
	block_nonce_bin = block_as_bin + '{:032b}'.format(nonce)
	hashHex = sha256(block_nonce_bin.encode())
	hashBin = bin(int(hashHex.hexdigest(), 16))[2:]

	if len(hashBin) <= 256 - difficulty:
		break
	
	nonce += 1

end_time = time.time()

print("\n")
print(f'Difficulty:   {difficulty}')
print(f'Elapsed Time: {end_time - start_time}')
print(f'Nonce:        {nonce}')
print(f'Nonce Binary: {"{:032b}".format(nonce)}')





# Return response 
response = queue_out.send_message(MessageBody=f'{0}', MessageAttributes={
		'ElapsedTime': {
			'StringValue': str(end_time - start_time),
			'DataType': 'Number',
		},
		'Nonce': {
			'StringValue': str(nonce),
			'DataType': 'String',
		},
		'NonceBinary': {
			'StringValue': str("{:032b}".format(nonce)),
			'DataType': 'String',
		} 
	})




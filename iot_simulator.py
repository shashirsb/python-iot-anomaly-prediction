import sys
import base64
import subprocess

filename = sys.argv[1]


# Open the file for reading
with open(filename, 'r') as file:
    # Read each line of the file
    for line in file:
        # Encode the line to base64
        encoded_line = base64.b64encode(line.encode())
        print('----------------1')
        # Call the shell command with the encoded line as an argument
        subprocess.call(['oci streaming stream message put --stream-id ',streamocid,' --messages \'[{\"key\":\"aW90Cg==\",\"value\":\"',encoded_line.decode(),'"}]\' --endpoint ',endpoint,' --debug'], shell=True)
        #subprocess.call(['your_shell_command', encoded_line.decode()])


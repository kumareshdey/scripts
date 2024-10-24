import os

# Define the base directory for the Excel files
base_dir = '/home/ubuntu/scripts/files/'
output_conf_file = 'supervisord.conf'

# Define the number of Excel chunks you have
start = 1
num_chunks = 50 # Update this based on the number of files you have

# Create the supervisord config file
with open(output_conf_file, 'w') as conf_file:
    # Write the global supervisord settings
    conf_file.write("[supervisord]\n")
    conf_file.write("logfile=/home/ubuntu/scripts/tmp/supervisord.log\n")
    conf_file.write("pidfile=/home/ubuntu/scripts/tmp/supervisord.pid\n\n")

    # Loop to generate a config section for each file
    for i in range(start, num_chunks + 1):
        if i in [2,3,4,5,6,7,8, 1, 9, 10, 19,20, 14, 18, 17, 13, 11, 15, 12, 26, 28, 25, 21, 24, 31, 34, 29, 23, 33, 22, 36]:
            continue
        program_name = f'script_{i}'
        excel_file = os.path.join(base_dir, f'output_chunk_{i}.xlsx')

        conf_file.write(f"[program:{program_name}]\n")
        conf_file.write(f"command=python3 fps_address_scraper.py {excel_file}\n")
        conf_file.write("autostart=true\n")
        conf_file.write("autorestart=false\n")
        conf_file.write(f"stdout_logfile=/home/ubuntu/scripts/tmp/{program_name}.log\n")
        conf_file.write(f"stderr_logfile=/home/ubuntu/scripts/tmp/{program_name}.err\n")
        conf_file.write("\n")

print(f"Supervisor configuration has been written to {output_conf_file}")

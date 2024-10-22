import os

# Define the base directory for the Excel files
base_dir = 'scripts/files/'
output_conf_file = 'supervisord.conf'

# Define the number of Excel chunks you have
num_chunks = 5  # Update this based on the number of files you have

# Create the supervisord config file
with open(output_conf_file, 'w') as conf_file:
    # Write the global supervisord settings
    conf_file.write("[supervisord]\n")
    conf_file.write("logfile=scripts/tmp/supervisord.log\n")
    conf_file.write("pidfile=scripts/tmp/supervisord.pid\n\n")

    # Loop to generate a config section for each file
    for i in range(1, num_chunks + 1):
        program_name = f'script_{i}'
        excel_file = os.path.join(base_dir, f'output_chunk_{i}.xlsx')

        conf_file.write(f"[program:{program_name}]\n")
        conf_file.write(f"command=python your_script.py {excel_file}\n")
        conf_file.write("autostart=true\n")
        conf_file.write("autorestart=true\n")
        conf_file.write(f"stdout_logfile=scripts/tmp/{program_name}.log\n")
        conf_file.write(f"stderr_logfile=scripts/tmp/{program_name}.err\n")
        conf_file.write("\n")

print(f"Supervisor configuration has been written to {output_conf_file}")
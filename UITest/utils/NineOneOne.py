import os


def change_proxy(exe_path, country, state, city, port):
    if os.path.exists(exe_path):
        cmd = f"{exe_path} -changeproxy/{country}/{state}/\"{city}\" -proxyport={port} -citynolimit"
        os.system(cmd)


def free_port(exe_path, port):
    if os.path.exists(exe_path):
        cmd = f"{exe_path} -freeport={port}"
        os.system(cmd)

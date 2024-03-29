# Docker Usage
Run the command in the same directory as `README.md`:
```bash
docker build -t distributed_compute:v1.0 . -f ./docker/Dockerfile
```

Then type:
```bash
docker images
```

You will see

|REPOSITORY|TAG|IMAGE ID|CREATED|SIZE|
|:---:|:---:|:---:|:---:|:---:|
|distributed_compute|v1.0|\<id\>|\<time\>|\<size\>

Type the following command to start this image with `bash`:
```bash
docker run -it distributed_compute:v1.0 /bin/bash
```

# Run
After start the image, type the command below to start:
```bash
cd /opt/2PLSF && python3.11 run.py
```

Afterwards, the log data will appear in the `/opt/2PLSF/data` directory, while the figures will appear in the `/opt/2PLSF/figure` directory.

# Change Log
- Deploy the code environment
    - docker/Dockerfile
- Test for the code
    - source/config.toml
    - source/requirements.txt
    - source/run.py/\<function benchmarks\>
- Draw the figures
    - source/run.py/\<function data_plot\>

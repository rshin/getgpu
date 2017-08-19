# Synopsis
Return the ID of a GPU which has no compute processes running on it.

GPUs which have compute processes running on it according to NVML, and GPUs for
which a different instance of `getgpu` has returned as available in the last
`--startup-time` seconds (30 by default), are treated as occupied.

# Usage
To install:
```bash
pip install --user git+https://github.com/rshin/getgpu
```

To set `CUDA_VISIBLE_DEVICES`:
```bash
G=$(getgpu) CUDA_VISIBLE_DEVICES=${G:?} python ...
```
Use of `${G:?}` ensures that if `getgpu` fails, then the rest of the command
does not run.

Run `getgpu --help` to see options.


# Development
```bash
pip install -e . dev
pre-commit install
```

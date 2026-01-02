#!/bin/bash
# This file is part of voice2machine.
#
# voice2machine is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# configura LD_LIBRARY_PATH para las librerías NVIDIA del venv
# necesario para que llama-cpp-python encuentre CUDA libs

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_PATH="${SCRIPT_DIR}/../apps/backend/venv"
SITE_PACKAGES="${VENV_PATH}/lib/python3.12/site-packages"

# lista de paquetes nvidia que contienen libs necesarias
NVIDIA_PACKAGES=(
    "cuda_runtime"
    "cublas"
    "cudnn"
    "cufft"
    "curand"
    "cusolver"
    "cusparse"
    "nvjitlink"
)

NVIDIA_LIB_PATHS=""
for pkg in "${NVIDIA_PACKAGES[@]}"; do
    lib_path="${SITE_PACKAGES}/nvidia/${pkg}/lib"
    if [ -d "$lib_path" ]; then
        if [ -z "$NVIDIA_LIB_PATHS" ]; then
            NVIDIA_LIB_PATHS="$lib_path"
        else
            NVIDIA_LIB_PATHS="${NVIDIA_LIB_PATHS}:${lib_path}"
        fi
    fi
done

export LD_LIBRARY_PATH="${LD_LIBRARY_PATH:+$LD_LIBRARY_PATH:}${NVIDIA_LIB_PATHS}"

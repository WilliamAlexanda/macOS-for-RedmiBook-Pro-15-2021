#!/bin/bash
# Rebuild WhateverXe 0.8.0 with the RedmiBook patches from source (macOS, Xcode command-line tools, Python 3).
# Pins match upstream CI: MacKernelSDK 05094e5e88cec7caedbfb35e8449ed0db94bf95b, Lilu 1.7.2.
set -euo pipefail
HERE=$(cd "$(dirname "$0")" && pwd)
W=${1:-$PWD/wex-build}
mkdir -p "$W" && cd "$W"
[ -d WhateverXe ] || git clone -q --branch 0.8.0 --depth 1 https://github.com/b00t0x/WhateverXe.git
[ -d MacKernelSDK ] || { git clone -q https://github.com/acidanthera/MacKernelSDK.git && git -C MacKernelSDK checkout -q 05094e5e88cec7caedbfb35e8449ed0db94bf95b; }
[ -d Lilu ] || git clone -q --branch 1.7.2 --depth 1 https://github.com/acidanthera/Lilu.git
cd WhateverXe
git apply "$HERE/all-in-one.patch"
ln -sfn ../MacKernelSDK MacKernelSDK
mkdir -p Lilu.kext/Contents/Resources
ln -sfn "$W/Lilu/Lilu/Headers" Lilu.kext/Contents/Resources/Headers
ln -sfn "$W/Lilu/Lilu/Library" Lilu.kext/Contents/Resources/Library
python3 tools/build.py --release --output build/RELEASE
echo "built: $W/WhateverXe/build/RELEASE/WhateverXe.kext"

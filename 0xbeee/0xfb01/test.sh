if [ ! -e micropython ]; then
git clone https://github.com/micropython/micropython.git
pushd micropython
# !!! update when badge-2024-firmware updates its submodule !!!
git checkout e0e9fbb17ed6fd06bb76e266ae554784c9c80804
popd
fi

which xtensa-elf-gcc > /dev/null 2>/dev/null
if [ $? -ne 0 ]; then
  if [ ! -e xtensa-esp-elf ]; then
    wget https://github.com/espressif/crosstool-NG/releases/download/esp-15.2.0_20251204/xtensa-esp-elf-15.2.0_20251204-x86_64-linux-gnu.tar.xz
    tar xf xtensa-esp-elf-15.2.0_20251204-x86_64-linux-gnu.tar.xz
  fi
  export PATH="$PATH:$(pwd)/xtensa-esp-elf/bin"
fi

pushd native
make
popd

mpremote cp -r ./metadata.json ./*.py native/native.mpy :/apps/stary_lora_test/
mpremote soft-reset exec 'import main'

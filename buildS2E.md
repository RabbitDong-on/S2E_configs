# Build S2E(C)
# Building the S2E Platform
Use vmware
```shell
1. apt-get install git

2. mkdir s2e
# 这里会有换行回车转换问题
# 可以在一个没问题的地方checkout对应分支，在cp资源到对应位置
3. git clone --recursive https://github.com/dslab-epfl/chef.git s2e/src

4. s2e/src/setup.sh --no-keep

5. s2e/src/ctl build
```
# Preparing VM Images for S2E
```shell
1. wget http://cdimage.debian.org/cdimage/archive/7.9.0-live/i386/iso-hybrid/debian-live-7.9.0-i386-standard.iso
# rootfs空间太小
2. ./ctl vm import --raw .iso Debian
# 使用iso 引导安装操作系统到disk.s2e
1. ./ctl vm create Debian 5120M
# 选install
2. ./ctl run -q=-cdrom -q .iso Debian kvm 
# for old version
qemu-img create -f raw -o size=10G chef_disk.raw
```
## Build network for guest and host
### Create tap in host
```shell
1. ip tuntap add dev tap0 mode tap
2. ip link set dev tap0 up
3. ip address add dev tap0 192.168.2.128/24
```
### Start qemu with -net option
```shell
# iso是用于去装系统的，装到disk.s2e这盘上
1. /home/mutu123/s2e/build/i386-release-normal/qemu/i386-softmmu/qemu-system-i386 -drive file=/home/mutu123/s2e/vm/MyBox/disk.s2e,if=virtio,format=raw -cpu pentium -m 2048M -net nic -net tap,ifname=tap0,script=no,downscript=no -enable-kvm -smp 2 -drive file=debian-live-7.7.0-i386-standard.iso
2. sudo ./ctl run -q=-drive -q file=debian-live-7.7.0-i386-standard.iso -n tap Debian kvm
3. sudo ./ctl run -n tap Debian kvm
```
### Configure net in guest
```shell
1. echo nameserver 114.114.114.114 > /etc/resolv.conf
2. /etc/init.d/networking restart
3. ip addr add 192.168.2.129/24 dev eth0
4. ip link set eth0 up
```
### Copy date from host to guest
```shell
# guest
1. vi /etc/ssh/sshd_config
PasswordAuthentication no --> yes
2. /etc/init.d/ssh restart
3. passwd
# host
# 移除之前的key
1. ssh-keygen -R 192.168.2.129
2. scp 即可
```
### Access net
```shell
# host
# 开启IP转发
1. echo 1 > /proc/sys/net/ipv4/ip_forward
2. route add -net 192.168.2.0 netmask 255.255.255.0 dev tap0
# 设置路由表
3. iptables -t nat -A POSTROUTING -s 192.168.2.0/24 -o eth0 -j MASQUERADE
# guest
1. route add default gw <host tap0 IP addr> dev eth0
```
目前Guest可以访问网络了
## Install packages
```shell
# debian 7 sources.list
deb http://mirrors.aliyun.com/debian-archive/debian/ wheezy main non-free contrib
deb http://mirrors.aliyun.com/debian-archive/debian/ wheezy-proposed-updates main non-free contrib
deb-src http://mirrors.aliyun.com/debian-archive/debian/ wheezy main non-free contrib
deb-src http://mirrors.aliyun.com/debian-archive/debian/ wheezy-proposed-updates main non-free contrib
```
### Update sources
```shell
# host
scp sources.list root@192.168.2.129:~
# guest
rm -rf /etc/apt/sources.list
cp ~/sources.list /etc/apt/
apt-get update
```
### Install packages
In prep mode:
```shell
apt-get install build-essential
```
### Reference
1. [Qemu网络配置](https://blog.csdn.net/jcf147/article/details/131290211)
2. [Debian源](https://www.cnblogs.com/tothk/p/16298181.html)

# S2E Workflow 
Need to save snapshot
```shell
# store iso to .s2e format
1. ./ctl run -n tap Debian prep
2. nc localhost 12345
3. savevm prepared
4. ./ctl run -n tap Debian:prepared sym
```
# Test a simple example
## Original Example
```c++
#include <stdio.h>
#include <string.h>

int main(void)
{
  char str[3];
  printf("Enter two characters: ");
  if(!fgets(str, sizeof(str), stdin))
    return 1;

  if(str[0] == '\n' || str[1] == '\n') {
    printf("Not enough characters\n");
  } else {
    if(str[0] >= 'a' && str[0] <= 'z')
      printf("First char is lowercase\n");
    else
      printf("First char is not lowercase\n");

    if(str[0] >= '0' && str[0] <= '9')
      printf("First char is a digit\n");
    else
      printf("First char is not a digit\n");

    if(str[0] == str[1])
      printf("First and second chars are the same\n");
    else
      printf("First and second chars are not the same\n");
  }
  return 0;
}
```
## Move .h file
```
scp s2e.h gendong@xxx:.
scp -r bits gendong@xxx:.
```
## Modified Example
```c++
#include <stdio.h>
#include <string.h>
#include "s2e.h"
int main(void)
{
  char str[3];
  // printf("Enter two characters: ");
  // if(!fgets(str, sizeof(str), stdin))
  //   return 1;
  s2e_enable_forking();
  s2e_make_symbolic(str,2,"str");

  if(str[0] == '\n' || str[1] == '\n') {
    printf("Not enough characters\n");
  } else {
    if(str[0] >= 'a' && str[0] <= 'z')
      printf("First char is lowercase\n");
    else
      printf("First char is not lowercase\n");

    if(str[0] >= '0' && str[0] <= '9')
      printf("First char is a digit\n");
    else
      printf("First char is not a digit\n");

    if(str[0] == str[1])
      printf("First and second chars are the same\n");
    else
      printf("First and second chars are not the same\n");
  }

  s2e_disable_forking();
  s2e_get_example(str,2);
  printf("'%c%c' %02x %02x\n", str[0], str[1],(unsigned char) str[0], (unsigned char) str[1]);
  s2e_kill_state(0,"program terminated");
  return 0;
}
```
## Output
```
' ' 00 00
```
# Equivalence Testing
## Original Example
```c++
#include <inttypes.h>
#include <s2e.h>

/**
 *  Computes x!
 *  If x > max, computes max!
 */
uint64_t factorial1(uint64_t x, uint64_t max) {
    uint64_t ret = 1;
    for (uint64_t i = 1; i<=x && i<=max; ++i) {
        ret = ret * i;
    }
    return ret;
}

/**
 *  Computes x!
 *  If x > max, computes max!
 */
uint64_t factorial2(uint64_t x, uint64_t max) {
    if (x > max) {
        return max;
    }

    if (x == 1) {
        return x;
    }
    return x * factorial2(x-1, max);
}

int main() {
    uint64_t x;
    uint64_t max = 10;

    //Make x symbolic
    s2e_make_symbolic(&x, sizeof(x), "x");
    s2e_enable_forking();

    uint64_t f1 = factorial1(x, max);
    uint64_t f2 = factorial2(x, max);

    //Check the equivalence of the two functions for each path
    s2e_assert(f1 == f2);

    //In case of success, terminate the state with the
    //appropriate message
    s2e_kill_state(0, "Success");
    return 0;
}
```
## Output
```
126 [State 0] State was terminated by opcode
            message: "Assertion failed: f1 == f2"
            status: 0x0
TestCaseGenerator: processTestCase of state 0 at address 0x804847f

              v0_x_0: 00 00 00 00 00 00 00 00, (int64_t) 0, (string) "........"
```
# Extending for Python
```shell
git clone https://github.com/dslab-epfl/chef-symbex-python.git
```
## Preparing the guest environment in KVM mode
In python-src/Chef/build
```shell
# host
scp -r guest gendong@192.168.2.19:~
# guest
# install cmake from source 
# reference: https://zhuanlan.zhihu.com/p/519732843
wget https://cmake.org/files/v3.2/cmake-3.2.0.tar.gz
tar -zxvf cmake-3.2.0.tar.gz
cd cmake-3.2.0
./configure
make
make install

# prepare llvm packages
tar -xf llvm-3.6.2.src.tar.xz
tar -xf compiler-rt-3.6.2.src.tar.xz
tar -xf cfe-3.6.2.src.tar.xz

mkdir llvm.src
cp -r llvm-3.6.2.src/* llvm.src/
mkdir llvm.src/tools/clang
cp -r cfe-3.6.2.src/* llvm.src/tools/clang/
mkdir llvm.src/projects/compiler-rt/
cp -r compiler-rt-3.6.2.src/* llvm.src/projects/compiler-rt/


cd guest/chef/
./build_llvm_i586.sh

export PATH=$PATH:/path/to/compiled/clang+llvm

# env
apt-get install libssl-dev
apt-get install zlib1g zlib1g-dev
apt-get install libyaml-dev
apt-get install libsqlite3-dev libreadline-dev libz2-dev

export S2E_GUEST=/path/to/guest

# guest
# prepare packages
# python-src/Chef/
cp -r /home/mutu/S2E_config/packages .
rm -rf Makefile.interp
cp /home/mutu/S2E_config/Makefile.interp .
rm -rf /example/requirement.txt
cp /home/mutu/S2E_config/requirement* example/
# python-src/Chef/build
mkdir build
cd build
make -f ../Makefile.interp
# pip -r --no-index --find-links 从本地下载
```
## Preparing the symbolic environment in Prep mode
Activate the Python environment:
```shell
source python-src/Chef/build/python-env/bin/activate
```
Enable symbolic execution mode:
```shell
export PYTHONSYMBEX=1
```
## Symbolic execution in SYM mode
Run the target symbolic test case.
```shell
python asplos_tests.py ArgparseTest
```



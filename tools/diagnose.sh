#!/bin/sh
env
echo LS_ROOT
ls -la /
echo LS_APP
ls -la /app || true
echo CMDLINE
tr '\0' ' ' < /proc/1/cmdline || true
sleep 300

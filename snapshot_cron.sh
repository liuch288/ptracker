#!/bin/bash
# Cron wrapper for ptracker snapshot
export PATH="/Users/boat/dev/ptracker/.venv/bin:/usr/local/bin:/usr/bin:/bin:$PATH"
/Users/boat/dev/ptracker/.venv/bin/ptracker snapshot take --no-show >> ~/.ptracker/cron_log.log 2>&1

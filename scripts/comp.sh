#!/bin/bash
if [[ "$OSTYPE" == "darwin"* ]]; then
        option=""
else
        option="sudo -u postgres "
fi

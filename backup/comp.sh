#!/bin/bash
if [[ "$OSTYPE" == "darwin"* ]]; then
        option=""
else
        option="-u postgres "
fi

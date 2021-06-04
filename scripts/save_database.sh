#!/bin/bash
sudo -u postgres pg_dump -F c -f backup/backup.db activities

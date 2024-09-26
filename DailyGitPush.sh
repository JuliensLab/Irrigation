#!/bin/bash
cd /home/pi/Irrigation
git add log.csv
git add console.log
git commit -m "Hourly log update"
git push origin master

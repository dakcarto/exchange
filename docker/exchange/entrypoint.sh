#!/bin/bash

set -e

manage='python /code/manage.py'
setup='python /code/setup.py'
maploom_static='/code/exchange/maploom/templates/maploom'
maploom_templates='exchange/maploom/templates'
# let the db intialize
if [[ $MAPLOOM_DEV == True ]]; then
  if [[ -d $maploom_static/assets ]]; then
    rm -r $maploom_static/assets
  fi
  ln -sf /code/vendor/maploom/bin/assets $maploom_static/assets
  if [[ -d $maploom_static/fonts ]]; then
    rm -r $maploom_static/fonts
  fi
  ln -sf /code/vendor/maploom/bin/fonts $maploom_static/fonts
  if [[ -f $maploom_templates/maploom/_maploom_map.html ]]; then
    rm $maploom_templates/maploom/_maploom_map.html
  fi
  ln -sf /code/vendor/maploom/bin/_maploom_map.html $maploom_templates/maploom/_maploom_map.html
  if [[ -f $maploom_templates/maploom/_maploom_map.html ]]; then
    rm $maploom_templates/maploom/_maploom_map.html
  fi
  ln -sf /code/vendor/maploom/bin/_maploom_map.html $maploom_templates/maploom/_maploom_map.html
  if [[ -f $maploom_templates/maps/maploom.html ]]; then
    rm $maploom_templates/maploom/_maploom_map.html
  fi
  ln -sf /code/vendor/maploom/bin/_maploom_map.html $maploom_templates/maps/maploom.html
fi
sleep 15
until $manage migrate account --noinput; do
  >&2 echo "db is unavailable - sleeping"
  sleep 5
done
$setup build_sphinx
$manage migrate --noinput
$manage collectstatic --noinput
$manage loaddata default_users
$manage loaddata base_resources
if [[ $DEV == True ]]; then
  $manage importservice http://data-test.boundlessgeo.io/geoserver/wms bcs-hosted-data WMS I
fi
$manage loaddata /code/docker/exchange/docker_oauth_apps.json
$manage rebuild_index
pip freeze
# app integration
plugins=()
# anywhere integration
if [[ -f /code/vendor/exchange-mobile-extension/setup.py ]]; then
   pip install /code/vendor/exchange-mobile-extension
   $manage loaddata /code/docker/exchange/anywhere.json
   plugins=("${plugins[@]}" "geonode_anywhere")
fi
if [[ -f /code/vendor/services/setup.py ]]; then
  pip install /code/vendor/services
  plugins=("${plugins[@]}" "worm")
fi
if [ "$plugins" ]; then
  ADDITIONAL_APPS=$(IFS=,; echo "${plugins[*]}")
fi
echo "Dev is set to $DEV"
supervisord -c /code/docker/exchange/supervisor.conf
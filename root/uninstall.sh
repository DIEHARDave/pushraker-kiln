#!/bin/sh
# pushraker-kiln: undo install.sh. Kiln runs it (root's copy) at
# DISABLE_PLUGIN / REMOVE_PLUGIN. The notification settings
# (printer_data/config/pushraker.conf, printer_data/pushraker.secrets)
# stay, for when the plugin comes back.
rm -f /data/ad5x/nginx/pushraker.conf /data/ad5x/nginx/pushraker.conf.old
nginx -t >/dev/null 2>&1 && nginx -s reload
echo "pushraker-kiln: settings page on port 82 removed"
exit 0

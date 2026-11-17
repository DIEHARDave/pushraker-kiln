#!/bin/sh
# pushraker-kiln: root's part, Kiln OS plugin API 1.6. Kiln runs it as
# root from /data/ad5x/plugins-root/pushraker (root's copy of root/) at
#   ENABLE_PLUGIN NAME=pushraker ROOT=1
# and, as update.sh, after each update that changes root/.
#
# It serves pushraker's settings page: an extra nginx server on port 82
# (/data/ad5x/nginx/pushraker.conf, which Kiln's nginx.conf includes)
# with the page from the plugin's python/pushraker/web and the Moonraker
# API and webcam locations the page uses. Kiln's port 80 server is in the
# read-only image, so the page gets its own port. nginx keeps the file
# across reboots: no boot script is needed.
set -e
PORT=82
CONF_DIR=/data/ad5x/nginx
CONF=$CONF_DIR/pushraker.conf
WEB=${PLUGIN_DIR:-/data/ad5x/plugins/pushraker}/python/pushraker/web

grep -qs 'include /data/ad5x/nginx/\*\.conf;' /etc/nginx/nginx.conf || {
	echo "install.sh: not the Kiln OS this was written for"
	echo "  (nginx.conf must include /data/ad5x/nginx/*.conf)"
	exit 1
}

mkdir -p $CONF_DIR
[ -f $CONF ] && cp $CONF $CONF.old
# Kiln's nginx is built without PCRE and without the rewrite module: no
# regex locations, no "return"
cat > $CONF.new <<EOF
# pushraker-kiln (root/install.sh): pushraker's settings page on port $PORT.
# The plugin rewrites this file: do not edit.
    server {
        listen $PORT;
        server_name _;

        location /notifications/ {
            alias $WEB/;
            index index.html;
            add_header Cache-Control "no-store";
        }
        location /webcam/ { proxy_pass http://127.0.0.1:8090/; include webcam_proxy.conf; }
        location /webcam2/ { proxy_pass http://127.0.0.1:8091/; include webcam_proxy.conf; }
        location /printer/ { include moonraker_proxy.conf; }
        location /access/ { include moonraker_proxy.conf; }
        location /machine/ { include moonraker_proxy.conf; }
        location /server/ { include moonraker_proxy.conf; }
    }
EOF
mv $CONF.new $CONF

if ! nginx -t 2>/tmp/pushraker-nginx.err; then
	cat /tmp/pushraker-nginx.err
	if [ -f $CONF.old ]; then mv $CONF.old $CONF; else rm -f $CONF; fi
	echo "install.sh: nginx refused the config; left as it was"
	exit 1
fi
rm -f $CONF.old /tmp/pushraker-nginx.err
nginx -s reload
echo "pushraker settings page: http://<printer>:$PORT/notifications/"

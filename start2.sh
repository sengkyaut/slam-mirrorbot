python3 -m bot &
aria2c --enable-rpc --check-certificate=false \
	--max-connection-per-server=10 --rpc-max-request-size=1024M --bt-max-peers=0 \
	--max-tries=20 --auto-file-renaming=true --reuse-uri=true --http-accept-gzip=true

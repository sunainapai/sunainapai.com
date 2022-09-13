# https://example.com/
server {
    listen 443 ssl;
    listen [::]:443 ssl;

    server_name sunainapai.com sunainapai;

    ssl_certificate /etc/letsencrypt/live/sunainapai.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/sunainapai.com/privkey.pem;

    root /var/www/sunainapai.com;
}

# https://www.example.com/ => https://example.com/
server {
    listen 443 ssl;
    listen [::]:443 ssl;

    server_name www.sunainapai.com www.sunainapai.in sunainapai.in;

    ssl_certificate /etc/letsencrypt/live/sunainapai.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/sunainapai.com/privkey.pem;

    return 301 https://sunainapai.com$request_uri;
}

# http://example.com/, http://www.example.com/ => https://example.com/
server {
    listen 80;
    listen [::]:80;
    server_name www.sunainapai.com www.sunainapai.in sunainapai.com sunainapai.in;
    return 301 https://sunainapai.com$request_uri;
}

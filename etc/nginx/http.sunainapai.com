# http://example.com/
server {
    listen 80;
    listen [::]:80;
    server_name sunainapai.com sunainapai;
    root /var/www/sunainapai.com;
}

# http://www.example.com/ => http://example.com/
server {
    listen 80;
    listen [::]:80;
    server_name www.sunainapai.com www.sunainapai.in sunainapai.in;
    return 301 http://sunainapai.com$request_uri;
}

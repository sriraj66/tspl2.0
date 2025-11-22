sudo apt update
sudo apt install certbot python3-certbot-nginx

sudo certbot certonly --standalone -d tspl.hattricksolution.in

sudo crontab -e

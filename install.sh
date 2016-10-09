root=`pwd`
sudo pip install django==1.9
sudo pip install MySQL-python
sudo pip install redis
sudo pip install celery
sudo pip install django-celery==3.1.17
sudo pip install uwsgi
sudo apt-get install redis-server supervisor salt-master salt-api salt-minion -y
sudo python manage.py collectstatic
sudo uwsgi -x uwsgi_socket.xml -b 32768
sudo cp django.conf /etc/nginx/sites-enabled/
sudo cp django_celery.conf /etc/supervisor/conf.d/
sudo sed -i "s#/home/mico/cmdb#$root#g" /etc/nginx/sites-enabled/django.conf
sudo sed -i "s#/home/mico/cmdb#$root#g" /etc/supervisor/conf.d/django_celery.conf
sudo /etc/init.d/nginx reload
sudo supervisorctl update

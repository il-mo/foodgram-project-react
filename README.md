# Проект Foodgram
Проект доступен по [адресу](http://51.250.7.207/recipes)
       
Сайт для публикации и поиска рецептов.


## Подготовка сервера (ubuntu):
* Клонируйте репозиторий себе на компьютер
```
git clone https://github.com/il-mo/foodgram-project-react
```

* Выполните вход на сервер и установите docker:
```
sudo apt install docker.io 
```
* Также необходимо установить docker-compose:
```
sudo curl -L "https://github.com/docker/compose/releases/download/1.29.2/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```
* Локально отредактируйте файл infra/nginx.conf. В строке server_name впишите ваш IP
* Скопируйте файлы docker-compose.yml и nginx.conf из директории infra на сервер:
```
scp docker-compose.yml <username>@<host>:/home/<username>/docker-compose.yml
scp nginx.conf <username>@<host>:/home/<username>/nginx.conf
```

* Cоздайте файл .env:
    ```
    DB_ENGINE=<django.db.backends.postgresql>
    DB_NAME=<имя базы данных postgres>
    POSTGRES_USER=<пользователь бд>
    POSTGRES_PASSWORD=<пароль>
    DB_HOST=<db>
    DB_PORT=<5432>
    ``` 
  ## Настройка Workflow:

* Workflow состоит из трёх шагов:
     - Проверка кода на соответствие PEP8
     - Docker-образ проекта пересобирается и пушится на Docker Hub.
     - Автоматический деплой на удаленный сервер.
  

* Для работы с Workflow добавьте в Secrets GitHub переменные окружения для работы:
    ```
    DB_ENGINE=<django.db.backends.postgresql>
    DB_NAME=<имя базы данных postgres>
    DB_USER=<пользователь бд>
    DB_PASSWORD=<пароль>
    DB_HOST=<db>
    DB_PORT=<5432>
    
    DOCKER_PASSWORD=<пароль от DockerHub>
    DOCKER_USERNAME=<имя пользователя>

    USER=<username для подключения к серверу>
    HOST=<IP сервера>
    PASSPHRASE=<пароль для сервера, если он установлен>
    SSH_KEY=<SSH ключ> (можно узнать, при помощи команды: cat ~/.ssh/id_rsa)
    ```


## Запуск проекта 

* После успешного деплоя, на сервере выполните команды:
    - Соберите статические файлы:
    ```
    sudo docker-compose exec backend python manage.py collectstatic --noinput
    ```
    - Примените миграции:
    ```
    sudo docker-compose exec backend python manage.py migrate --noinput
    ```
    - Создать суперпользователя Django:
    ```
    sudo docker-compose exec backend python manage.py createsuperuser
    ```
    - Проект будет доступен по вашему IP
  
## Cтек технологий

<img height="40" src="https://www.python.org/static/community_logos/python-logo-generic.svg">
<img height="40" src="https://static.djangoproject.com/img/logos/django-logo-negative.svg" >
<img height="40" src="https://seeklogo.com/images/P/postgresql-logo-6DBC096ED4-seeklogo.com.png">
<img height="40" src="https://upload.wikimedia.org/wikipedia/commons/4/4e/Docker_%28container_engine%29_logo.svg">

## Об авторе

-_-
 

from pathlib import Path
import os


from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(os.path.join(BASE_DIR, ".env"))



SECRET_KEY = 'django-insecure-+nymptal3fy%x0)m*0tj^pti9vvx!^js&xzg6v+xy6)2s*tkzm'

DEBUG = os.getenv("DEBUG") == "True"

ALLOWED_HOSTS = ['*','localhost', '127.0.0.1','.ecare.support','ecare.support','*.ecare.support', 'www.care.ecare.support','www.ecare.support']


SHARED_APPS = [ 
    'django_tenants',  
    'django.contrib.contenttypes',  
    'django.contrib.sessions',     
    'django.contrib.messages',     
    'django.contrib.staticfiles',  
    'django_crontab',               
    'django_celery_beat',   
    'django_extensions',   
    'django.contrib.humanize',   
    'django.contrib.sites',
    'django.contrib.auth',   
    'django.contrib.admin',  
    'accounts',
    'clients',   
     

]

TENANT_APPS = [  
 
    'core', 
    'leavemanagement',
    'appointments',
    'billing',
    'inventory',
    'lab_tests',
    'medical_records',
    'patients',
    'visitors',
    'messaging',
    'payment_gateway',
    'facilities',
    'finance',
    'accounting',
    'logistics',
    'purchase',
    'supplier',
    'product',
    'workspace',
 
  
    
]


INSTALLED_APPS = list(SHARED_APPS) + [app for app in TENANT_APPS if app not in SHARED_APPS]

SITE_ID = 1

TENANT_MODEL = "clients.Client"  
TENANT_DOMAIN_MODEL = "clients.Domain"  
DATABASE_ROUTERS = ("django_tenants.routers.TenantSyncRouter",)
PUBLIC_SCHEMA_NAME = 'public'

AUTH_USER_MODEL = 'accounts.CustomUser' 



AUTHENTICATION_BACKENDS = [
    'accounts.backends.TenantAuthenticationBackend',  # Custom tenant-aware backend
    'django.contrib.auth.backends.ModelBackend',  # Default Django backend
]




MIDDLEWARE = [
    'clients.middleware.BypassTenantMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',  
    'django_tenants.middleware.TenantMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'clients.middleware.CustomTenantAuthMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]


ROOT_URLCONF = 'hospitalcare.urls'
PUBLIC_SCHEMA_URLCONF = "hospitalcare.public_urls"
TEMPLATES = [
    {
       'BACKEND': 'django.template.backends.django.DjangoTemplates',
       'DIRS': [os.path.join(BASE_DIR, 'templates')], 
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'accounts.context_processors.user_info',
                'accounts.context_processors.unread_notifications',
            ],
        },
    },
]

WSGI_APPLICATION = 'hospitalcare.wsgi.application'




# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.sqlite3',
#         'NAME': BASE_DIR / 'db.sqlite3',
#     }
# }


DATABASES = {
    'default': {
        'ENGINE': 'django_tenants.postgresql_backend',
        'NAME': os.getenv('DB_NAME'),
        'USER': os.getenv('DB_USER'),
        'PASSWORD': os.getenv('DB_PASSWORD'),
        'HOST': os.getenv('DB_HOST'),
        'PORT': os.getenv('DB_PORT'),
    }
}


# AUTH_PASSWORD_VALIDATORS = [
#     {
#         'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
#     },
#     {
#         'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
#     },
#     {
#         'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
#     },
#     {
#         'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
#     },
# ]





import os
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'ERROR',
            'class': 'logging.FileHandler',
            'filename': os.path.join(BASE_DIR, 'error.log'),  # Save error logs to this file
            'formatter': 'verbose',
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file', 'console'],  # Logs errors to file and console
            'level': 'ERROR',  # Log ERROR level and above
            'propagate': True,
        },
        'inventory': {  # Replace 'inventory' with your app's name
            'handlers': ['file', 'console'],  # Logs DEBUG and above for this app
            'level': 'DEBUG',
            'propagate': False,
        },
    },
}




CELERY_BROKER_URL = 'redis://172.28.62.68:6379/0'  # Replace with your WSL IP address
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_BACKEND = 'redis://172.28.62.68:6379/0'  # Same IP for result backend


MAX_PENALTY_CAP = 500.00



LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
TIME_ZONE = 'Asia/Dhaka'
USE_I18N = True
USE_TZ = True

import os
STATIC_URL = "/static/"
STATICFILES_DIRS = [os.path.join(BASE_DIR, "static")]
STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")
MEDIA_URL = "/media/"
MEDIA_ROOT = os.path.join(BASE_DIR, "media/")


LOGIN_REDIRECT_URL = '/clients/tenant_expire_check/'
LOGIN_URL = 'accounts:login'




EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
MESSAGE_STORAGE = 'django.contrib.messages.storage.session.SessionStorage'




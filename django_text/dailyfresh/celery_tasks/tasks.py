from django.core.mail import send_mail
from django.conf import settings
from celery import Celery
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer


#创建一个celery的实例对象
app = Celery('celery.celery_task', broker='redis://192.168.43.182:6379/8')

@app.task
def send_active_mail(to_mail, token, username):
    # TODO
    my_email = '26437559@163.com'
    html_message = """<h1>%s,欢迎您成为天天生鲜注册会员，请点击以下链接激活您的账户:</h1>
                           <br/><a href="http://127.0.0.1:8000/user/active/s%">
                           http://127.0.0.1:8000/user/active/s%</a>""" % (username, token, token)
    send_mail('active message', '', my_email, to_mail, html_message=html_message)




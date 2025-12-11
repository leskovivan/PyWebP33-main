import binascii
from django.http import HttpResponse, HttpResponseNotAllowed, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render
from django.template import loader
from .forms.demo_form import DemoForm
from .forms.styled_form import StyledForm
from .forms.delivery_form import DeliveryForm
from .forms.signup_form import SignupForm
from datetime import datetime
from .helper import * 
from .models import *
import base64,uuid
# технічно представлення - це функції, які приймають
# запит (request) та формують відповідь (response)

def auth(request) :
    authHeader =request.headers.get('Authorization')
    if not authHeader:
        return HttpResponse("Missing 'Authorization' header", status = 401)
    authScheme = "Basic"
    if not authHeader.startswith(authScheme):
        return HttpResponse("Invalid authorization scheme", status = 401)
    credentials = authHeader[len(authScheme):]
    if len(credentials) <4:
        return HttpResponse("Invalid credentials", status = 401)
    try:
        user_pass = base64.b64decode(credentials).decode("utf-8")
    except Exception as err:
        return HttpResponse("Decode error" + str(err), status = 401)
    parts = user_pass.split(":", 1)
    if len(parts) != 2:
        return HttpResponse("Invalid credentials format", status = 401)
    login, password = parts
    try:
        acces = Access.objects.get(login = login)
    except Access.DoesNotExist:
        return HttpResponse("Invalid login", status = 401)
    _salt = acces.salt
    _dk = dk(password, _salt)
    if _dk != acces.dk:
        return HttpResponse("Invalid password", status = 401)
    acces.token = str(uuid.uuid4())
    acces.token_d=datetime.now()
    return HttpResponse(acces.token, status = 200)



def test(request):
    authHeader = request.headers.get("Authorization")
    if not authHeader:
        return HttpResponse("Missing 'Authorization' header", status=401)
    if not authHeader.startswith("Bearer "):
        return HttpResponse("Invalid authorization scheme", status=401)
    # Вилучити токен і перевірити що в ньому 36 символи = якщо ні 403
    token = authHeader[len("Bearer "):]
    if len(token) != 36:
        return HttpResponse("Invalid token length", status=403)
    # Перевірити що у бд є access з відповідними токеном
    try:
        acces = Access.objects.get(token=token)
    except Access.DoesNotExist:
        return HttpResponse("Invalid token", status=403)
    return HttpResponse("It does work", status=200)

def clonning(request) :
    template = loader.get_template('clonning.html')
    return HttpResponse( template.render() )


def form_delivery(request) :
    template = loader.get_template('form_delivery.html')
    if request.method == 'GET' :
        context = {
            'form': DeliveryForm()
        }
    elif request.method == 'POST' :
        form = DeliveryForm(request.POST)
        context = {
            'form': form
        }
    return HttpResponse( template.render(context=context, request=request) )


def form_styled(request) :
    template = loader.get_template('form_styled.html')
    if request.method == 'GET' :
        context = {
            'form': StyledForm()
        }
    elif request.method == 'POST' :
        form = StyledForm(request.POST)
        context = {
            'form': form
        }
    return HttpResponse( template.render(context=context, request=request) )


def forms(request) :
    if request.method == 'GET' :
        template = loader.get_template('forms.html')
        context = {
            'form': DemoForm()
        }
    elif request.method == 'POST' :
        form = DemoForm(request.POST)
        context = {
            'form': form
        }
        template = loader.get_template('form_ok.html' if form.is_valid() else 'forms.html')
    else :
        return HttpResponseNotAllowed()
    
    return HttpResponse( template.render(context=context, request=request) )


def hello(request) :
    return HttpResponse("Hello, world!")


def home(request) :
    template = loader.get_template('home.html')
    context = {
        'x': 10,
        'y': 20,
        'page_title': 'Домашня',
        'page_header': 'Розробка вебдодатків з використанням Python',
        'now': datetime.now().strftime("%H:%M:%S %d.%m.%Y")
    }
    return HttpResponse( template.render(context, request) )


def layouting(request) :
    template = loader.get_template('layouting.html')
    return HttpResponse( template.render() )


def models(request) :
    template = loader.get_template('models.html')
    return HttpResponse( template.render(request=request) )


def params(request) :    
    context = {
        'params': str(request.GET),
        'user': request.GET.get('user', 'Немає даних'),
        'q': request.GET.get('q', 'Немає даних'),
    }
    about = request.GET.get('about', None)
    if about == 'GET' :
        context['about_get'] = " (метод не має тіла і вживається як запит на читання)"
    elif about == 'POST' :
        context['about_post'] = " (метод може мати тіло і вживається як запит на створення)"
    '''Д.З. Створити посилання-підказки для НТТР-методів PUT, PATCH, DELETE
    (аналогічно створеним на занятті для методів GET, POST).
    До звіту додавати скріншоти'''
    template = loader.get_template('params.html')
    return HttpResponse( template.render(context, request) )


@csrf_exempt
def seed(request) :
    if request.method == 'PATCH' :
        res = {
            "guest": "",
            "admin-role": "",
            "test-user": "",
            "test-access": ""
        }
        try :
            guest = Role.objects.get(name="Self registered")
        except Role.DoesNotExist :
            guest = Role()
            guest.name = "Self registered"
            res["guest"] = "created"
        else :
            res["guest"] = "updated"
        guest.create_level = guest.read_level = guest.update_level = guest.delete_level = 0
        guest.save()

        try :
            admin = Role.objects.get(name="Root Administrator")    
        except Role.DoesNotExist :
            admin = Role()
            admin.name = "Root Administrator"
            res["admin-role"] = "created"
        else : 
            res["admin-role"] = "updated"
        admin.create_level = admin.read_level = admin.update_level = admin.delete_level = 1
        admin.save()
        
        # Д.З. Розширити метод сідування, додати тестового користувача
        # з гостьовою роллю. Якщо немає - створювати, якщо є - оновлювати 
        # логін та пароль
        try :
            test_user = User.objects.get(first_name="Test", last_name='Guest')    
        except User.DoesNotExist :
            test_user = User()
            test_user.first_name = "Test"
            test_user.last_name  = 'Guest'
            test_user.email      = 'guest@test.local'
            test_user.phone      = '1111111111'
            test_user.save()
            res["test-user"] = "created"
        else : 
            res["test-user"] = "updated"
            # Оновлюємо email/phone при кожному seed (опціонально)
            test_user.email = 'guest@test.local'
            test_user.phone = '1111111111'
            test_user.save()

        try :
            test_access = Access.objects.get(user=test_user)    
        except Access.DoesNotExist :
            test_access = Access()
            res["test-access"] = "created"
        else : 
            res["test-access"] = "updated"
        
        # Завжди оновлюємо логін та пароль
        _test_salt = salt()
        _test_dk = dk('guest123', _test_salt)
        test_access.user  = test_user
        test_access.role  = guest  # Використовуємо гостьову роль "Self registered"
        test_access.login = 'guest'
        test_access.salt  = _test_salt
        test_access.dk    = _test_dk
        test_access.save()
        
        return JsonResponse(res)
    
    else :
        template = loader.get_template('seed.html')
        return HttpResponse( template.render() )


def signup(request) :
    template = loader.get_template('signup.html')
    if request.method == 'GET' :
        context = {
            'form': SignupForm()
        }
    elif request.method == 'POST' :
        form = SignupForm(request.POST)
        context = {
            'form': form,
            'is_ok': form.is_valid()
        }
        if form.is_valid() :
            form_data = form.cleaned_data
            _salt = salt()
            _dk = dk(form_data['password'], _salt)
            
            user = User()
            user.first_name = form_data['first_name']
            user.last_name  = form_data['last_name']
            user.email      = form_data['email']
            user.phone      = form_data['phone']
            user.birthdate  = form_data['birthdate']
            user.save()

            user_access = Access()
            user_access.user  = user
            user_access.role  = Role.objects.get(name="Self registered")
            user_access.login = form_data['login']
            user_access.salt  = _salt
            user_access.dk    = _dk
            user_access.save()

            context['user'] = user
            context['user_access'] = user_access

    # context['salt'] = salt()    
    # context['dk'] = dk("123", "456")    
    return HttpResponse( template.render(request=request, context=context) )


def statics(request) :
    template = loader.get_template('statics.html')
    return HttpResponse( template.render() )
